# Contributing to StockAlert Python SDK

We love your input! We want to make contributing to this project as easy and transparent as possible.

## Development Process

1. Fork the repo and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/python-sdk.git
cd python-sdk

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy stockalert
```

## Code Style

- We use [Ruff](https://github.com/astral-sh/ruff) for linting
- We use [Black](https://github.com/psf/black) formatting (line length: 100)
- We use type hints everywhere
- Write docstrings for all public functions

## Testing

- Write tests for any new functionality
- Maintain or improve code coverage
- Run the full test suite before submitting

## Pull Request Process

1. Update the README.md with details of changes to the interface
2. Update the CHANGELOG.md with your changes
3. The PR will be merged once you have the sign-off of maintainers

## Any contributions you make will be under the MIT Software License
When you submit code changes, your submissions are understood to be under the same [MIT License](LICENSE) that covers the project.
