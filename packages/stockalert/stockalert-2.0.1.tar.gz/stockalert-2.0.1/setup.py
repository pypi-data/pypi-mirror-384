
from setuptools import find_packages, setup

# Read version
with open("stockalert/__version__.py") as f:
    about = {}
    exec(f.read(), about)
    __version__ = about["__version__"]

# Minimal README for PyPI
with open("README-pypi.md", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="stockalert",
    version=__version__,
    author="StockAlert.pro",
    author_email="support@stockalert.pro",
    description="Official Python SDK for StockAlert.pro API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stockalert-pro/python-sdk",
    entry_points={
        "console_scripts": [
            "stockalert=stockalert.cli.main:main",
        ],
    },
    packages=find_packages(exclude=["tests*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "typing-extensions>=4.0.0;python_version<'3.10'",
    ],
    extras_require={
        "async": ["httpx>=0.24.0"],
        "dev": [
            "pre-commit>=3.0.0",
            "pytest>=7.0.0",
            "types-requests>=2.31.0,",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.21.0",
            "ruff>=0.1.0",
            "mypy>=1.0.0",
            "httpx>=0.24.0",  # For async tests
        ],
    },
)
