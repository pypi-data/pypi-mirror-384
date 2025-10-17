"""
OpenAI Wrapper Package - No Pydantic Dependencies
A simple wrapper for calling OpenAI API without Pydantic.
"""

from .client import ask_ai_question

__all__ = ['ask_ai_question']
__version__ = '0.1.0'
