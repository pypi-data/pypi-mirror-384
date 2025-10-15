import os
from setuptools import setup, find_packages

setup(
    name="nys_client",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.1",
        "python-dotenv>=1.0.0",
        "typing-extensions>=4.12.2",
        "pydantic>=1.10.0,<2.0.0",
        "fastapi-pagination>=0.12.0",
        "nys_constants>=0.1.0",
        "nys_schemas>=0.1.0",
    ],
    python_requires=">=3.8",
    author="Noyes",
    author_email="dev@noyes.com",
    description="Python client library for the Noyes API",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/noyes/nys_client",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
) 