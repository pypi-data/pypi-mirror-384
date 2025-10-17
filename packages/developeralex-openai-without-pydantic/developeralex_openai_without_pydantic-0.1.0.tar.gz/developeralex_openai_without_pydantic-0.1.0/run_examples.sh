#!/bin/bash
# Convenience script to run examples with virtual environment activated

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
source .venv/bin/activate

# Show menu
echo "======================================"
echo "OpenAI Without Pydantic - Examples"
echo "======================================"
echo ""
echo "Select an example to run:"
echo "  1) Basic Usage"
echo "  2) Advanced Usage"
echo "  3) Batch Processing"
echo "  4) All Examples"
echo "  q) Quit"
echo ""
read -p "Enter your choice [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "Running Basic Usage Example..."
        echo "======================================"
        python examples/basic_usage.py
        ;;
    2)
        echo ""
        echo "Running Advanced Usage Example..."
        echo "======================================"
        python examples/advanced_usage.py
        ;;
    3)
        echo ""
        echo "Running Batch Processing Example..."
        echo "======================================"
        python examples/batch_processing.py
        ;;
    4)
        echo ""
        echo "Running All Examples..."
        echo "======================================"
        echo ""
        echo ">>> BASIC USAGE <<<"
        python examples/basic_usage.py
        echo ""
        echo ""
        echo ">>> ADVANCED USAGE <<<"
        python examples/advanced_usage.py
        echo ""
        echo ""
        echo ">>> BATCH PROCESSING <<<"
        python examples/batch_processing.py
        ;;
    q|Q)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice. Exiting..."
        exit 1
        ;;
esac

echo ""
echo "======================================"
echo "Done!"
echo "======================================"
