import os
from setuptools import setup, find_packages

setup(
    name="nys_schemas",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pydantic>=1.10.0,<2.0.0",
        "email-validator>=1.1.3",
        "nys_constants>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "isort>=5.0",
            "flake8>=3.9",
            "mypy>=0.910",
        ],
    },
    python_requires=">=3.8",
    author="Noyes",
    author_email="dev@noyes.com",
    description="Shared Pydantic schemas for Noyes packages",
    long_description=open("README.md").read() if os.path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    url="https://github.com/noyes/nys_schemas",
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