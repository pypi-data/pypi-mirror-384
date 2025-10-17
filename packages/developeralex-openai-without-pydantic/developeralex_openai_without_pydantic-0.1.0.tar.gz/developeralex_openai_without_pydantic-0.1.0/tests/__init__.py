"""
Test configuration for pytest
"""
import sys
import os

# Add parent directory to path to allow importing openai_wrapper
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
