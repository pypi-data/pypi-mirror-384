# Publishing to PyPI

This guide will walk you through the steps to publish the `openai-without-pydantic` package to PyPI.

## Prerequisites

1. **Python** installed (3.7 or higher)
2. **PyPI Account**: Create accounts on both:
   - [Test PyPI](https://test.pypi.org/account/register/) (for testing)
   - [PyPI](https://pypi.org/account/register/) (for production)
3. **API Tokens**: Generate API tokens for both platforms:
   - Test PyPI: https://test.pypi.org/manage/account/#api-tokens
   - PyPI: https://pypi.org/manage/account/#api-tokens

## Installation of Build Tools

Install the required build and upload tools:

```bash
pip install --upgrade build twine
```

## Step 1: Update Version Number

Before publishing, update the version number in `openai_wrapper/__init__.py`:

```python
__version__ = '0.1.1'  # Increment as needed
```

Version numbering follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible functionality additions
- **PATCH** version for backwards-compatible bug fixes

## Step 2: Clean Previous Builds

Remove any old build artifacts:

```bash
rm -rf build/ dist/ *.egg-info
```

## Step 3: Build the Package

Build the source distribution and wheel:

```bash
python -m build
```

This creates two files in the `dist/` directory:
- `openai-without-pydantic-X.Y.Z.tar.gz` (source distribution)
- `openai_without_pydantic-X.Y.Z-py3-none-any.whl` (wheel distribution)

## Step 4: Test on Test PyPI (Recommended)

Before publishing to the real PyPI, test on Test PyPI:

### Upload to Test PyPI:

```bash
python -m twine upload --repository testpypi dist/*
```

You'll be prompted for:
- **Username**: `__token__`
- **Password**: Your Test PyPI API token (including the `pypi-` prefix)

### Install from Test PyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ --no-deps openai-without-pydantic
```

### Test the Installation:

```python
from openai_wrapper import ask_ai_question

# Test the function
response = ask_ai_question(
    input_text="Python is a programming language.",
    question_asked="What is Python?"
)
print(response)
```

## Step 5: Publish to PyPI

Once you've verified everything works on Test PyPI:

```bash
python -m twine upload dist/*
```

You'll be prompted for:
- **Username**: `__token__`
- **Password**: Your PyPI API token (including the `pypi-` prefix)

## Step 6: Verify the Upload

Check your package on PyPI:
- https://pypi.org/project/openai-without-pydantic/

Install from PyPI to verify:

```bash
pip install openai-without-pydantic
```

## Using PyPI Tokens with .pypirc (Optional)

To avoid entering credentials each time, create a `~/.pypirc` file:

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YourPyPITokenHere

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YourTestPyPITokenHere
```

**Important**: Keep this file secure! Add it to `.gitignore` if it's in your project directory.

## Publishing Checklist

Before each release, ensure:

- [ ] Version number is updated in `openai_wrapper/__init__.py`
- [ ] README.md is up to date
- [ ] All tests pass (if you have tests)
- [ ] CHANGELOG is updated (if you maintain one)
- [ ] Git commits are pushed to GitHub
- [ ] Git tag created for the version: `git tag v0.1.0 && git push origin v0.1.0`
- [ ] Package builds successfully: `python -m build`
- [ ] Package tested on Test PyPI
- [ ] Package uploaded to PyPI
- [ ] Installation from PyPI verified

## Updating the Package

To publish a new version:

1. Make your code changes
2. Update the version in `openai_wrapper/__init__.py`
3. Clean old builds: `rm -rf build/ dist/ *.egg-info`
4. Build: `python -m build`
5. Upload: `python -m twine upload dist/*`

## Common Issues

### "File already exists"
- You cannot overwrite existing versions on PyPI
- Increment the version number and rebuild

### "Invalid distribution file"
- Ensure you've cleaned old builds before creating new ones
- Run `rm -rf build/ dist/ *.egg-info` and rebuild

### "403 Forbidden"
- Check your API token is correct
- Ensure username is `__token__` (not your PyPI username)
- Verify the token has upload permissions

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)

## Automating with GitHub Actions (Advanced)

You can automate PyPI publishing using GitHub Actions. Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Then add your PyPI token as a secret named `PYPI_API_TOKEN` in your GitHub repository settings.
