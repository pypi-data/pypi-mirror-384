import os
from setuptools import setup, find_packages

setup(
    name="nys_constants",
    version="0.1.0",
    packages=find_packages(),
    author="Noyes",
    author_email="dev@noyes.com",
    description="Core constants and enums for the Noyes system",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/noyes/nys_constants",
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
    python_requires=">=3.8",
)
