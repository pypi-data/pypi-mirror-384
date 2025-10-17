#!/bin/bash
# Quick script to run tests

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

source .venv/bin/activate
pytest tests/ -v
