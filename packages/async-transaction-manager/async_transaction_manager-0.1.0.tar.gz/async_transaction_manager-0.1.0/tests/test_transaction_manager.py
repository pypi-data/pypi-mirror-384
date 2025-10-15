import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock
import logging
from src.transaction_manager import TransactionManager, TransactionStepStatus, TransactionHook

logging.getLogger('src.transaction_manager').addHandler(logging.NullHandler())

class TestTransactionManager(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.transaction_id = "test_transaction_123"
        self.operation_name = "Test Operation"
        self.tx_manager = TransactionManager(self.transaction_id, self.operation_name)

    async def test_successful_transaction(self):
        mock_execute_func1 = AsyncMock(return_value={"data": "step1_data"})
        mock_rollback_func1 = AsyncMock()
        mock_execute_func2 = AsyncMock(return_value={"data": "step2_data"})
        mock_rollback_func2 = AsyncMock()

        async with self.tx_manager as tx:
            result1 = await tx.add_step("Step1", mock_execute_func1, mock_rollback_func1)
            result2 = await tx.add_step("Step2", mock_execute_func2, mock_rollback_func2)

        self.assertEqual(result1, {"data": "step1_data"})
        self.assertEqual(result2, {"data": "step2_data"})

        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.COMPLETED)
        self.assertEqual(self.tx_manager.steps[1].status, TransactionStepStatus.COMPLETED)

        mock_rollback_func1.assert_not_called()
        mock_rollback_func2.assert_not_called()

        summary = self.tx_manager.get_transaction_summary()
        self.assertEqual(summary["transaction_id"], self.transaction_id)
        self.assertEqual(summary["operation_name"], self.operation_name)
        self.assertEqual(summary["total_steps"], 2)
        self.assertEqual(summary["completed_steps"], 2)
        self.assertEqual(summary["failed_steps"], 0)
        self.assertEqual(summary["rolled_back_steps"], 0)
        self.assertEqual(summary["rollback_errors"], 0)
        self.assertFalse(summary["is_rolling_back"])

    async def test_transaction_failure_and_rollback(self):
        mock_execute_func1 = AsyncMock(return_value={"data": "step1_data", "rollback_data": {"id": 1}})
        mock_rollback_func1 = AsyncMock()
        mock_execute_func2 = AsyncMock(side_effect=ValueError("Step 2 failed"))
        mock_rollback_func2 = AsyncMock()

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step("Step1", mock_execute_func1, mock_rollback_func1)
                await tx.add_step("Step2", mock_execute_func2, mock_rollback_func2)

        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLED_BACK)
        self.assertEqual(self.tx_manager.steps[1].status, TransactionStepStatus.FAILED)
        self.assertTrue(self.tx_manager.is_rolling_back)

        mock_rollback_func1.assert_called_once_with(id=1)
        mock_rollback_func2.assert_not_called()

        summary = self.tx_manager.get_transaction_summary()
        self.assertEqual(summary["completed_steps"], 0)
        self.assertEqual(summary["failed_steps"], 1)
        self.assertEqual(summary["rolled_back_steps"], 1)
        self.assertEqual(summary["rollback_errors"], 0)
        self.assertTrue(summary["is_rolling_back"])

    async def test_rollback_function_failure(self):
        mock_execute_func1 = AsyncMock(return_value={"data": "step1_data", "rollback_data": {"id": 1}})
        mock_rollback_func1 = AsyncMock(side_effect=RuntimeError("Rollback failed"))
        mock_execute_func2 = AsyncMock(side_effect=ValueError("Step 2 failed"))
        mock_rollback_func2 = AsyncMock()

        with self.assertRaises(RuntimeError):
            async with self.tx_manager as tx:
                await tx.add_step("Step1", mock_execute_func1, mock_rollback_func1)
                await tx.add_step("Step2", mock_execute_func2, mock_rollback_func2)

        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLBACK_FAILED)
        self.assertEqual(self.tx_manager.steps[1].status, TransactionStepStatus.FAILED)
        self.assertTrue(self.tx_manager.is_rolling_back)
        self.assertEqual(len(self.tx_manager.rollback_errors), 1)
        self.assertIsInstance(self.tx_manager.rollback_errors[0], RuntimeError)

        mock_rollback_func1.assert_called_once_with(id=1)
        
    async def test_no_rollback_func(self):
        mock_execute_func1 = AsyncMock(return_value={"data": "step1_data"})
        mock_execute_func2 = AsyncMock(side_effect=ValueError("Step 2 failed"))

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step("Step1", mock_execute_func1)
                await tx.add_step("Step2", mock_execute_func2)
                raise ValueError("Simulated failure")

        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.COMPLETED)
        self.assertEqual(self.tx_manager.steps[1].status, TransactionStepStatus.FAILED)
        self.assertTrue(self.tx_manager.is_rolling_back)
        self.assertEqual(len(self.tx_manager.rollback_errors), 0)

    async def test_timeout_execute_func(self):
        mock_execute_func = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_rollback_func = AsyncMock()

        with self.assertRaises(asyncio.TimeoutError):
            async with self.tx_manager as tx:
                await tx.add_step("TimedStep", mock_execute_func, mock_rollback_func, timeout=0.1)

        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.FAILED)
        self.assertIsInstance(self.tx_manager.steps[0].error, asyncio.TimeoutError)
        mock_rollback_func.assert_not_called()


    async def test_timeout_rollback_func(self):
        mock_execute_func = AsyncMock(return_value={"data": "executed", "rollback_data": {"id": 1}})
        mock_rollback_func = AsyncMock(side_effect=asyncio.TimeoutError)

        with self.assertRaises(RuntimeError):
            async with self.tx_manager as tx:
                await tx.add_step("Step1", mock_execute_func, mock_rollback_func)
                await tx.add_step("FailingStep", AsyncMock(side_effect=ValueError("Failure")))
        
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLBACK_FAILED)
        self.assertIsInstance(self.tx_manager.rollback_errors[0], asyncio.TimeoutError)
        mock_execute_func.assert_called_once()
        mock_rollback_func.assert_called_once()
    
    async def test_retry_execute_success(self):
        mock_execute_func = AsyncMock(side_effect=[ValueError("Transient"), {"data": "success"}])
        mock_rollback_func = AsyncMock()

        async with self.tx_manager as tx:
            result = await tx.add_step("RetryStep", mock_execute_func, mock_rollback_func, max_retries=1, retry_interval=0.01)
        
        self.assertEqual(result, {"data": "success"})
        mock_execute_func.call_count = 2
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.COMPLETED)
        mock_rollback_func.assert_not_called()

    async def test_retry_execute_failure(self):
        mock_execute_func = AsyncMock(side_effect=[ValueError("Transient"), ValueError("Still failing")])
        mock_rollback_func = AsyncMock()

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step("RetryStep", mock_execute_func, mock_rollback_func, max_retries=1, retry_interval=0.01)

        self.assertEqual(mock_execute_func.call_count, 2)
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.FAILED)
        mock_rollback_func.assert_not_called()

    async def test_retry_rollback_success(self):
        mock_execute_func = AsyncMock(return_value={"data": "executed", "rollback_data": {"id": 1}})
        mock_rollback_func = AsyncMock(side_effect=[RuntimeError("Rollback transient"), None])

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step("Step1", mock_execute_func, mock_rollback_func, max_retries=1, retry_interval=0.01)
                await tx.add_step("FailingStep", AsyncMock(side_effect=ValueError("Failure")))

        mock_execute_func.assert_called_once()
        self.assertEqual(mock_rollback_func.call_count, 2)
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLED_BACK)
        self.assertEqual(len(self.tx_manager.rollback_errors), 0)

    async def test_retry_rollback_failure(self):
        mock_execute_func = AsyncMock(return_value={"data": "executed", "rollback_data": {"id": 1}})
        mock_rollback_func = AsyncMock(side_effect=[RuntimeError("Rollback transient"), RuntimeError("Rollback still failing")])

        with self.assertRaises(RuntimeError):
            async with self.tx_manager as tx:
                await tx.add_step("Step1", mock_execute_func, mock_rollback_func, max_retries=1, retry_interval=0.01)
                await tx.add_step("FailingStep", AsyncMock(side_effect=ValueError("Failure")))
        
        mock_execute_func.assert_called_once()
        self.assertEqual(mock_rollback_func.call_count, 2)
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLBACK_FAILED)
        self.assertEqual(len(self.tx_manager.rollback_errors), 1)
        self.assertIsInstance(self.tx_manager.rollback_errors[0], RuntimeError)
    
    async def test_rollback_args_override(self):
        mock_execute = AsyncMock(return_value={'data': 'executed', 'rollback_args': ("rollback_arg",),
                    'override_args':True,'rollback_data': {'exec_id': 123}})
        mock_rollback = AsyncMock()
        mock_execute2 = AsyncMock(return_value={'data': 'executed', 'rollback_args': ("rollback_arg",),
                    'override_args':True,'rollback_data': {'exec_id': 123}})
        mock_rollback2 = AsyncMock()

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step(
                    "StepWithOverride",
                    mock_execute,
                    mock_rollback,
                    args=("original_arg",),
                    kwargs={'original_kwarg': 'value'},
                )
                await tx.add_step(
                    "StepWithOverride2",
                    mock_execute2,
                    mock_rollback2,
                    args=("original_arg2",),
                    kwargs={'original_kwarg': 'value2'},
                )
                
                self.tx_manager.steps[-1].status = TransactionStepStatus.FAILED
                self.tx_manager.steps[-1].error = ValueError("Simulated failure")
                raise ValueError("Simulated failure")

        mock_execute.assert_called_once_with(*("original_arg",), **{'original_kwarg': 'value'})
        mock_rollback.assert_called_once_with(*("rollback_arg",), original_kwarg="value", exec_id=123)
        mock_execute2.assert_called_once_with(*("original_arg2",), **{'original_kwarg': 'value2'})
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLED_BACK)

    async def test_rollback_args_no_override(self):
        mock_execute = AsyncMock(return_value={'data': 'executed', 'rollback_args': ("rollback_arg",),
                    'override_args':False,'rollback_data': {'exec_id': 123}})
        mock_rollback = AsyncMock()
        mock_execute2 = AsyncMock(return_value={'data': 'executed', 'rollback_args': ("rollback_arg",),
                    'override_args':False,'rollback_data': {'exec_id': 123}})
        mock_rollback2 = AsyncMock()

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step(
                    "StepNoOverride",
                    mock_execute,
                    mock_rollback,
                    args=("original_arg",),
                    kwargs={'original_kwarg': 'value'},
                    
                )
                await tx.add_step(
                    "StepNoOverride2",
                    mock_execute2,
                    mock_rollback2,
                    args=("original_arg2",),
                    kwargs={'original_kwarg': 'value2'},
                    
                )
                
                self.tx_manager.steps[-1].status = TransactionStepStatus.FAILED
                self.tx_manager.steps[-1].error = ValueError("Simulated failure")
                raise ValueError("Simulated failure")

        mock_execute.assert_called_once_with("original_arg", original_kwarg="value")
        mock_execute2.assert_called_once_with("original_arg2", original_kwarg="value2")
        mock_rollback.assert_called_once_with(*("original_arg",), original_kwarg="value", exec_id=123)
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLED_BACK)

    async def test_custom_rollback_args_from_result(self):
        mock_execute = AsyncMock(return_value={'data': 'executed', 'rollback_data': {'id': 456}, 'rollback_args': ('custom_rb_arg',), 'override_args': True})
        mock_rollback = AsyncMock()
        mock_execute2 = AsyncMock(return_value={'data': 'executed', 'rollback_data': {'id': 456}, 'rollback_args': ('custom_rb_arg',), 'override_args': True})
        mock_rollback2 = AsyncMock()

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step(
                    "StepWithDynamicRollbackArgs",
                    mock_execute,
                    mock_rollback,
                    args=("initial_arg",)
                )
                await tx.add_step(
                    "StepWithDynamicRollbackArgs2",
                    mock_execute2,
                    mock_rollback2,
                    args=("initial_arg2",)
                )
                
                self.tx_manager.steps[-1].status = TransactionStepStatus.FAILED
                self.tx_manager.steps[-1].error = ValueError("Simulated failure")
                raise ValueError("Simulated failure")

        mock_execute.assert_called_once_with("initial_arg")
        mock_execute2.assert_called_once_with("initial_arg2")
        mock_rollback.assert_called_once_with(*('custom_rb_arg',), id=456)
        self.assertEqual(self.tx_manager.steps[0].status, TransactionStepStatus.ROLLED_BACK)

    async def test_hooks_called_correctly(self):
        mock_hook = MagicMock(spec=TransactionHook)
        self.tx_manager.register_hook(mock_hook)

        mock_execute1 = AsyncMock(return_value={"data": "step1"})
        mock_rollback1 = AsyncMock()
        mock_execute2 = AsyncMock(side_effect=ValueError("Failure"))
        mock_rollback2 = AsyncMock()

        with self.assertRaises(ValueError):
            async with self.tx_manager as tx:
                await tx.add_step("HookStep1", mock_execute1, mock_rollback1)
                await tx.add_step("HookStep2", mock_execute2, mock_rollback2)

        mock_hook.on_transaction_start.assert_called_once_with(self.transaction_id, self.operation_name)
        
        
        mock_hook.on_step_execute.assert_any_call(self.tx_manager.steps[0])
        mock_hook.on_step_success.assert_any_call(self.tx_manager.steps[0])
        
        mock_hook.on_step_execute.assert_any_call(self.tx_manager.steps[1])
        mock_hook.on_step_failure.assert_any_call(self.tx_manager.steps[1])

        mock_hook.on_rollback_start.assert_called_once_with(self.transaction_id)
        mock_hook.on_step_rollback.assert_called_once_with(self.tx_manager.steps[0])

        mock_hook.on_transaction_complete.assert_called_once()
        args, _ = mock_hook.on_transaction_complete.call_args
        self.assertEqual(args[0], self.transaction_id)
        self.assertFalse(args[1])

