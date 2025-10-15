import asyncio
from typing import List, Dict, Any, Optional, Callable, Awaitable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class TransactionHook(ABC):
    """
    Abstract base class for transaction hooks. Implementations can override
    these methods to execute custom logic at different points in the
    transaction lifecycle.
    """
    
    async def on_transaction_start(self, transaction_id: str, operation_name: str):
        pass
        
    async def on_step_execute(self, step: "TransactionStep"): # Forward reference
        pass
        
    async def on_step_success(self, step: "TransactionStep"):
        pass
        
    async def on_step_failure(self, step: "TransactionStep"):
        pass
        
    async def on_rollback_start(self, transaction_id: str):
        pass
        
    async def on_step_rollback(self, step: "TransactionStep"):
        pass
        
    async def on_step_rollback_failure(self, step: "TransactionStep"):
        pass
        
    async def on_transaction_complete(self, transaction_id: str, success: bool, summary: Dict[str, Any]):
        pass


class TransactionStepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    ROLLBACK_FAILED = "rollback_failed"


@dataclass
class TransactionStep:
    name: str
    execute_func: Callable[..., Awaitable[Any]]
    rollback_func: Optional[Callable[..., Awaitable[Any]]] = None
    execute_args: Any = field(default_factory=tuple)
    execute_kwargs: Any = field(default_factory=dict)
    status: TransactionStepStatus = TransactionStepStatus.PENDING
    result: Any = None
    error: Optional[Exception] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    rollback_data: Optional[Dict[str, Any]] = None
    rollback_args: Optional[Tuple] = None
    override_args: Optional[bool] = False
    operation_name: Optional[str] = None
    timeout: Optional[int] = None
    max_retries: int = 0
    retry_interval: float = 0.5 # seconds


class TransactionManager():
    """
    Manages transactional operations with automatic rollback on failure.
    
    Example:
        async with TransactionManager("create_vdi_account") as tx:
            # Step 1: Create user
            user_result = await tx.add_step(
                "create_user",
                user_service.create_user,
                rollback_func=user_service.delete_user,
                username="john.doe",
                email="john@example.com"
            )
            
            # Step 2: Create VM
            vm_result = await tx.add_step(
                "create_vm",
                vm_service.create_vm,
                rollback_func=vm_service.delete_vm,
                vm_name="john-vm",
                user_id=user_result["user_id"]
            )
            
            # If any step fails, all previous steps are automatically rolled back
    """
    
    def __init__(self, transaction_id: str, operation_name: Optional[str] = None):
        super().__init__()
        self.transaction_id = transaction_id
        self.operation_name = operation_name or transaction_id
        self.steps: List[TransactionStep] = []
        self.current_step_index = -1
        self.is_rolling_back = False
        self.rollback_errors: List[Exception] = []
        self.hooks: List[TransactionHook] = []
        
    @staticmethod
    def configure_logging(level: int = logging.INFO, handler: Optional[logging.Handler] = None):
        """Configures the logging for the TransactionManager library.
        
        This method allows users to customize the logging behavior of the library.
        By default, the library uses a NullHandler, which means no logs will be emitted
        unless a handler is configured.
        
        Args:
            level (int): The logging level to set (e.g., logging.INFO, logging.DEBUG).
                         Defaults to logging.INFO.
            handler (Optional[logging.Handler]): An optional logging handler to add.
                                                  If None, a StreamHandler will be configured.
        """
        # Remove existing NullHandler if present
        if isinstance(logger.handlers[0], logging.NullHandler):
            logger.removeHandler(logger.handlers[0])
        
        logger.setLevel(level)
        if handler:
            logger.addHandler(handler)
        else:
            stream_handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            
    def register_hook(self, hook: TransactionHook):
        """Registers a transaction hook.
        
        Args:
            hook (TransactionHook): An instance of a TransactionHook to register.
        """
        self.hooks.append(hook)
        
    async def __aenter__(self):
        """Start the transaction.
        Logs the start of the transaction and returns the TransactionManager instance.
        """
        logger.info(
            "Transaction started",
            extra={
                "transaction_id": self.transaction_id,
                "operation": self.operation_name
            }
        )
        for hook in self.hooks:
            await hook.on_transaction_start(self.transaction_id, self.operation_name)
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """End the transaction and handle rollback if needed.
        If an exception occurred during the transaction or any step failed, a rollback is initiated.
        Logs transaction completion or failure and rollback initiation.
        """
        transaction_successful = True
        final_exception = None
        
        if exc_type is not None or any(step.status == TransactionStepStatus.FAILED for step in self.steps):
            transaction_successful = False
            
            # Determine the primary failure exception
            failed_steps = [step for step in self.steps if step.status == TransactionStepStatus.FAILED]
            if failed_steps:
                final_exception = failed_steps[0].error
            elif exc_val:
                final_exception = exc_val
                
            await self._rollback()
            
            if self.rollback_errors:
                rollback_error_message = "Transaction rollback completed with errors."
                if final_exception:
                    # Chain original exception with rollback errors
                    final_exception = RuntimeError(f"{rollback_error_message} Original error: {final_exception}")
                else:
                    final_exception = RuntimeError(rollback_error_message)
            # If no rollback errors, and there was an original exception, that's the one to raise
            elif final_exception:
                pass # final_exception is already set from failed_steps or exc_val
        
        for hook in self.hooks:
            await hook.on_transaction_complete(self.transaction_id, transaction_successful, self.get_transaction_summary())
        
        if final_exception:
            raise final_exception
            
        return not transaction_successful # Suppress exception if transaction was successful
    
    async def add_step(
        self,
        name: str,
        execute_func: Callable[..., Awaitable[Any]],
        rollback_func: Optional[Callable[..., Awaitable[Any]]] = None,
        timeout: Optional[int] = None,
        max_retries: int = 0,
        retry_interval: float = 0.5,
        args: Any = None,
        kwargs: Any = None,
    ) -> Any:
        """Adds a step to the transaction and executes it.
        
        Args:
            name (str): The name of the step.
            execute_func (Callable[..., Awaitable[Any]]): The asynchronous function to execute.
            rollback_func (Optional[Callable[..., Awaitable[Any]]]): The asynchronous function to call for rollback if the transaction fails. Defaults to None.
            timeout (Optional[int]): The maximum time in seconds to wait for the step to complete. Defaults to None (no timeout).
            max_retries (int): The maximum number of times to retry the step's execution or rollback if it fails. Defaults to 0 (no retries).
            retry_interval (float): The base interval in seconds between retries, which will be exponentially increased. Defaults to 0.5.
            *args: Positional arguments to pass to the execute_func.
            **kwargs: Keyword arguments to pass to the execute_func.
            
        Returns:
            Any: The result of the execute_func.
            
        Raises:
            asyncio.TimeoutError: If the step execution exceeds the specified timeout.
            Exception: If the execute_func raises an unexpected exception.
        """
       
        step = TransactionStep(
            name=name,
            execute_func=execute_func,
            rollback_func=rollback_func,
            execute_args=args if args else (),
            execute_kwargs=kwargs if kwargs else {},
            operation_name=self.operation_name,
            timeout=timeout,
            max_retries=max_retries,
            retry_interval=retry_interval
        )
        
        self.steps.append(step)
        self.current_step_index += 1
        
        return await self._execute_step(step, timeout)
    
    async def _execute_step(self, step: TransactionStep, timeout: Optional[int] = None) -> Any:
        """Execute a single transaction step."""
        step.status = TransactionStepStatus.IN_PROGRESS
        step.started_at = datetime.now(timezone.utc)
        
        for attempt_num in range(step.max_retries + 1):
            logger.info(
                f"Executing step: {step.name} (attempt {attempt_num + 1}/{step.max_retries + 1})",
                extra={
                    "transaction_id": self.transaction_id,
                    "step": step.name,
                    "step_index": self.current_step_index,
                    "timeout": timeout,
                    "attempt": attempt_num + 1
                }
            )
            for hook in self.hooks:
                await hook.on_step_execute(step)
            
            try:
                if timeout:
                    result = await asyncio.wait_for(step.execute_func(*step.execute_args, **step.execute_kwargs), timeout=timeout)
                else:
                    result = await step.execute_func(*step.execute_args, **step.execute_kwargs)
                
                step.result = result
                step.status = TransactionStepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                
                # Extract rollback data if the result contains it
                if isinstance(result, dict):
                    if "rollback_data" in result:
                        step.rollback_data = result["rollback_data"]
                    if "rollback_args" in result:
                        step.rollback_args = result["rollback_args"]
                    if "override_args" in result:
                        step.override_args = bool(result["override_args"])
                    
                logger.info(
                    f"Step completed: {step.name}",
                    extra={
                        "transaction_id": self.transaction_id,
                        "step": step.name,
                        "duration_ms": (step.completed_at - step.started_at).total_seconds() * 1000
                    }
                )
                for hook in self.hooks:
                    await hook.on_step_success(step)
                return result
                
            except (asyncio.TimeoutError, Exception) as e:
                for hook in self.hooks:
                    await hook.on_step_failure(step)
                if attempt_num < step.max_retries:
                    sleep_time = step.retry_interval * (2 ** attempt_num)
                    logger.warning(
                        f"Step {step.name} failed (attempt {attempt_num + 1}/{step.max_retries + 1}). Retrying in {sleep_time:.2f} seconds...",
                        extra={
                            "transaction_id": self.transaction_id,
                            "step": step.name,
                            "error": str(e),
                            "retry_in": sleep_time
                        }
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    step.error = e
                    step.status = TransactionStepStatus.FAILED
                    step.completed_at = datetime.now(timezone.utc)
                    logger.error(
                        f"Step {step.name} failed after {step.max_retries + 1} attempts",
                        exc_info=True,
                        extra={
                            "transaction_id": self.transaction_id,
                            "step": step.name,
                            "error": str(e)
                        }
                    )
                    return None
        return None # Should not be reached if step completes or fails after retries
    
    async def _rollback(self):
        """Rollback all completed steps in reverse order.
        Iterates through successfully completed steps in reverse order and attempts to call their rollback functions.
        Logs the initiation and completion (with or without errors) of the rollback process.
        """
        if self.is_rolling_back:
            return  # Already rolling back
            
        completed_steps = [s for s in self.steps if s.status == TransactionStepStatus.COMPLETED]
        if not completed_steps:
            self.is_rolling_back = False # No steps to roll back
            return
            
        self.is_rolling_back = True
        
        logger.warning(
            "Initiating transaction rollback",
            extra={
                "transaction_id": self.transaction_id,
                "steps_to_rollback": len(completed_steps)
            }
        )
        for hook in self.hooks:
            await hook.on_rollback_start(self.transaction_id)
        
        # Rollback completed steps in reverse order
        completed_steps = [s for s in self.steps if s.status == TransactionStepStatus.COMPLETED]
        completed_steps.reverse()
        
        for step in completed_steps:
            if step.rollback_func:
                await self._rollback_step(step, step.timeout)
        
        if self.rollback_errors:
            logger.error(
                "Transaction rollback completed with errors",
                extra={
                    "transaction_id": self.transaction_id,
                    "rollback_errors": len(self.rollback_errors),
                    "errors": [str(e) for e in self.rollback_errors]
                }
            )
        else:
            logger.info(
                "Transaction rollback completed successfully",
                extra={
                    "transaction_id": self.transaction_id,
                    "steps_rolled_back": len(completed_steps)
                }
            )
    
    async def _rollback_step(self, step: TransactionStep, timeout: Optional[int] = None) -> Any:
        """Rollback a single step.
        Attempts to call the rollback function for a given step, applying any rollback data.
        Logs the success or failure of the rollback attempt.
        """
        for attempt_num in range(step.max_retries + 1):
            logger.info(
                f"Rolling back step: {step.name} (attempt {attempt_num + 1}/{step.max_retries + 1})",
                extra={
                    "transaction_id": self.transaction_id,
                    "step": step.name,
                    "timeout": timeout,
                    "attempt": attempt_num + 1
                }
            )
            try:
                # Prepare rollback arguments
                rollback_kwargs = step.execute_kwargs.copy() # Use execute_kwargs for rollback
                
                if step.rollback_data:
                    rollback_kwargs.update(step.rollback_data)
                
                if step.override_args:
                    rollback_args = step.rollback_args
                else:
                    rollback_args = step.execute_args # Use execute_args for rollback
                    
                if timeout:
                    await asyncio.wait_for(step.rollback_func(*rollback_args, **rollback_kwargs), timeout=timeout)
                else:
                    await step.rollback_func(*rollback_args, **rollback_kwargs)
                
                step.status = TransactionStepStatus.ROLLED_BACK
                
                logger.info(
                    f"Successfully rolled back step: {step.name}",
                    extra={
                        "transaction_id": self.transaction_id,
                        "step": step.name
                    }
                )
                for hook in self.hooks:
                    await hook.on_step_rollback(step)
                return
            except (asyncio.TimeoutError, Exception) as e:
                for hook in self.hooks:
                    await hook.on_step_rollback_failure(step)
                if attempt_num < step.max_retries:
                    sleep_time = step.retry_interval * (2 ** attempt_num)
                    logger.warning(
                        f"Rollback for step {step.name} failed (attempt {attempt_num + 1}/{step.max_retries + 1}). Retrying in {sleep_time:.2f} seconds...",
                        exc_info=True,
                        extra={
                            "transaction_id": self.transaction_id,
                            "step": step.name,
                            "error": str(e),
                            "retry_in": sleep_time
                        }
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(
                        f"Failed to rollback step: {step.name} after {step.max_retries + 1} attempts",
                        exc_info=True,
                        extra={
                            "transaction_id": self.transaction_id,
                            "step": step.name,
                            "error": str(e)
                        }
                    )
                    step.status = TransactionStepStatus.ROLLBACK_FAILED
                    self.rollback_errors.append(e)
        
    
    def get_transaction_summary(self) -> Dict[str, Any]:
        """Get a summary of the transaction state."""
        return {
            "transaction_id": self.transaction_id,
            "operation_name": self.operation_name,
            "total_steps": len(self.steps),
            "completed_steps": len([s for s in self.steps if s.status == TransactionStepStatus.COMPLETED]),
            "failed_steps": len([s for s in self.steps if s.status == TransactionStepStatus.FAILED]),
            "rolled_back_steps": len([s for s in self.steps if s.status == TransactionStepStatus.ROLLED_BACK]),
            "rollback_errors": len(self.rollback_errors),
            "is_rolling_back": self.is_rolling_back,
            "steps": [
                {
                    "name": step.name,
                    "status": step.status.value,
                    "started_at": step.started_at.isoformat() if step.started_at else None,
                    "completed_at": step.completed_at.isoformat() if step.completed_at else None,
                    "error": str(step.error) if step.error else None,
                    "operation_name": step.operation_name,
                    "timeout": step.timeout
                }
                for step in self.steps
            ]
        }
