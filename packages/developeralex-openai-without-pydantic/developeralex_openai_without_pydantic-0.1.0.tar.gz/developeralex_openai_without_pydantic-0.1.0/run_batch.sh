#!/bin/bash
# Quick script to run batch processing example

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

source .venv/bin/activate
python examples/batch_processing.py
