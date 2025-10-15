import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="async-transaction-manager",
    version="0.1.2",
    author="Amir Alaghmandan",
    author_email="amir.alaghmand@gmail.com",
    description="A robust asynchronous transaction management library for Python functions.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amirmotlagh/transaction-manager",
    packages=setuptools.find_packages(exclude=["tests*"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Framework :: AsyncIO",
    ],
    python_requires='>=3.8',
    install_requires=[],
    project_urls={
        'Bug Tracker': 'https://github.com/amirmotlagh/transaction-manager/issues',
    },
)
