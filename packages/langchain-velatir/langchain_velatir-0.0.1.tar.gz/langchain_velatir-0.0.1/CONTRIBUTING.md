# Contributing to langchain-velatir

Thank you for your interest in contributing to langchain-velatir! This document provides guidelines and instructions for contributing.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/velatir/langchain-velatir.git
   cd langchain-velatir
   ```

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

## Running Tests

Run the test suite:

```bash
pytest tests/
```

Run tests with coverage:

```bash
pytest --cov=langchain_velatir tests/
```

## Code Style

We use `black` for code formatting and `ruff` for linting:

```bash
# Format code
black langchain_velatir/ tests/

# Check linting
ruff check langchain_velatir/ tests/

# Auto-fix linting issues
ruff check --fix langchain_velatir/ tests/
```

## Type Checking

We use `mypy` for type checking:

```bash
mypy langchain_velatir/
```

## Pull Request Process

1. **Fork the repository** and create your branch from `main`
2. **Make your changes** with clear commit messages
3. **Add tests** for any new functionality
4. **Update documentation** including docstrings and README
5. **Run all checks**:
   ```bash
   black langchain_velatir/ tests/
   ruff check langchain_velatir/ tests/
   mypy langchain_velatir/
   pytest tests/
   ```
6. **Submit a pull request** with a clear description

## Guidelines

### Code Guidelines

- Follow PEP 8 style guide
- Write clear, self-documenting code
- Add type hints to all functions
- Include docstrings for all public APIs
- Keep functions focused and concise

### Testing Guidelines

- Write tests for all new features
- Ensure all tests pass before submitting PR
- Aim for high code coverage
- Use descriptive test names
- Mock external dependencies

### Documentation Guidelines

- Update README.md for user-facing changes
- Add docstrings to all public APIs
- Include examples for new features
- Keep documentation clear and concise

## Reporting Bugs

Report bugs via [GitHub Issues](https://github.com/velatir/langchain-velatir/issues):

1. Use a clear, descriptive title
2. Describe the expected behavior
3. Describe the actual behavior
4. Provide steps to reproduce
5. Include error messages and stack traces
6. Specify your environment (Python version, OS, etc.)

## Feature Requests

We welcome feature requests! Please:

1. Check existing issues first
2. Provide a clear use case
3. Explain why it would benefit users
4. Include examples if possible

## Questions

For questions:
- Check the [documentation](https://www.velatir.com/docs)
- Contact us at hello@velatir.com

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Help maintain a positive community

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
