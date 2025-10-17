# Quick Start Guide

Get started with OpenAI Without Pydantic in 3 easy steps!

## Step 1: Setup (First Time Only)

```bash
# Clone the repository (if you haven't already)
git clone https://github.com/DeveloperAlex/pypi_OpenAI_Without_Pydantic.git
cd pypi_OpenAI_Without_Pydantic

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install the package in editable mode
pip install -e .

# Set your OpenAI API key
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

## Step 2: Run Examples

### Option A: Use Convenience Scripts (Easiest!)

```bash
# Interactive menu to choose examples
./run_examples.sh

# Or run specific examples directly
./run_basic.sh       # Basic usage
./run_advanced.sh    # Advanced features
./run_batch.sh       # Batch processing
```

### Option B: Manual Python Execution

```bash
# Activate virtual environment first
source .venv/bin/activate

# Then run examples
python examples/basic_usage.py
python examples/advanced_usage.py
python examples/batch_processing.py
```

## Step 3: Use in Your Own Code

```python
from openai_wrapper import ask_ai_question

response = ask_ai_question(
    input_text="Your context here...",
    question_asked="Your question here?"
)
print(response)
```

## Running Tests

```bash
# Use convenience script
./run_tests.sh

# Or manually
source .venv/bin/activate
pytest tests/ -v
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'openai_wrapper'"
```bash
source .venv/bin/activate
pip install -e .
```

### "Permission denied" when running scripts
```bash
chmod +x run_*.sh
```

### "API key not found"
Make sure you have set `OPENAI_API_KEY` in your `.env` file or as an environment variable:
```bash
export OPENAI_API_KEY='your-key-here'
```

## What's Next?

- 📖 Read the [full README](README.md) for detailed documentation
- 💡 Explore [examples/](examples/) for more use cases
- 🤝 See [CONTRIBUTING.md](CONTRIBUTING.md) to contribute
- 🔒 Review [SECURITY.md](SECURITY.md) for security best practices
- 📦 Check [PUBLISHING.md](PUBLISHING.md) to publish to PyPI

## Common Commands

```bash
# Install package
pip install -e .

# Run all examples
./run_examples.sh

# Run tests
./run_tests.sh

# Activate virtual environment
source .venv/bin/activate

# Deactivate virtual environment
deactivate
```

Happy coding! 🚀
