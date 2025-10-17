# Convenience Scripts

These shell scripts make it easy to run examples and tests without manually activating the virtual environment.

## Available Scripts

### 📋 Interactive Menu
```bash
./run_examples.sh
```
Displays an interactive menu to choose which example to run:
- Basic Usage
- Advanced Usage  
- Batch Processing
- All Examples

### 🚀 Quick Run Scripts

Run individual examples directly:

```bash
./run_basic.sh       # Run basic usage example
./run_advanced.sh    # Run advanced usage example
./run_batch.sh       # Run batch processing example
```

### ✅ Testing

```bash
./run_tests.sh       # Run the test suite
```

## How They Work

Each script:
1. Automatically activates the virtual environment (`.venv`)
2. Runs the specified example or test
3. Works from any directory

## Requirements

- Virtual environment must be set up (`.venv/`)
- Package must be installed in editable mode: `pip install -e .`
- API key must be set in `.env` file or as environment variable

## Troubleshooting

**"Permission denied"**
```bash
chmod +x run_*.sh
```

**"Virtual environment not found"**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

**"Module not found"**
```bash
source .venv/bin/activate
pip install -e .
```
