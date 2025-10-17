# Contributing to OpenAI Without Pydantic

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Running Tests](#running-tests)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)

## Code of Conduct

This project follows a Code of Conduct to ensure a welcoming environment for all contributors. Please be respectful and constructive in all interactions.

## How Can I Contribute?

### Reporting Bugs

If you find a bug, please create an issue with:
- Clear, descriptive title
- Steps to reproduce the issue
- Expected vs actual behavior
- Python version and OS
- Code samples if applicable

### Suggesting Enhancements

Enhancement suggestions are welcome! Please create an issue with:
- Clear description of the feature
- Use cases and examples
- Why this would be useful to other users

### Pull Requests

We actively welcome pull requests for:
- Bug fixes
- Documentation improvements
- New features (please discuss in an issue first)
- Test coverage improvements
- Performance optimizations

## Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/pypi_OpenAI_Without_Pydantic.git
   cd pypi_OpenAI_Without_Pydantic
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   
   # Linux/macOS
   source .venv/bin/activate
   
   # Windows
   .venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Set up your environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Running Tests

Run the test suite:
```bash
pytest tests/ -v
```

Run tests with coverage:
```bash
pytest tests/ -v --cov=openai_wrapper --cov-report=term-missing
```

Run tests on specific Python version:
```bash
python3.10 -m pytest tests/
```

## Submitting Changes

1. **Create a new branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write clear, readable code
   - Add tests for new functionality
   - Update documentation as needed
   - Follow the coding standards below

3. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "Clear description of changes"
   ```
   
   Use conventional commit messages:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation changes
   - `test:` for test additions/changes
   - `refactor:` for code refactoring
   - `chore:` for maintenance tasks

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**
   - Go to the original repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template with details

## Coding Standards

### Python Style
- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints where applicable
- Maximum line length: 100 characters
- Use docstrings for functions and classes

### Documentation
- Update README.md for user-facing changes
- Update CHANGELOG.md following [Keep a Changelog](https://keepachangelog.com/)
- Add docstrings to new functions:
  ```python
  def function_name(param: str) -> bool:
      """
      Brief description.
      
      Args:
          param: Description of parameter
          
      Returns:
          Description of return value
          
      Raises:
          ExceptionType: When this exception occurs
      """
  ```

### Testing
- Write tests for all new functionality
- Maintain or improve test coverage
- Use descriptive test names
- Test both success and error cases

### Commit Messages
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Keep commits focused and atomic

## Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows PEP 8 style guidelines
- [ ] Type hints are added where applicable
- [ ] Tests are added/updated and passing
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (if applicable)
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains what and why

## Questions?

If you have questions about contributing, feel free to:
- Open an issue for discussion
- Check existing issues and PRs
- Review the README.md for general information

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🎉
