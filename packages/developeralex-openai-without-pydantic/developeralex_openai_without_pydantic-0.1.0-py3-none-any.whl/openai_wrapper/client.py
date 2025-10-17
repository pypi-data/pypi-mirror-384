"""
OpenAI Client without Pydantic
Simple wrapper for OpenAI API calls using direct HTTP requests.
No dependencies on OpenAI SDK or Pydantic.
"""

import os
import json
from typing import Optional, Dict, Any
import requests


def ask_ai_question(
    input_text: str,
    question_asked: str,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    timeout: int = 30
) -> str:
    """
    Ask AI a question based on provided input text.
    
    This function calls the OpenAI API directly using HTTP requests,
    completely bypassing the OpenAI SDK and its Pydantic dependencies.
    
    Args:
        input_text: The context/text to use for answering the question
        question_asked: The question to ask about the input_text
        api_key: OpenAI API key (defaults to OPENAI_API_KEY environment variable)
        model: The OpenAI model to use (defaults to OPENAI_MODEL env var or "gpt-4o-mini")
        temperature: Sampling temperature 0-2 (defaults to OPENAI_TEMPERATURE env var or 0.7)
        max_tokens: Maximum tokens in the response (optional)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        str: The AI's response to the question
        
    Raises:
        ValueError: If API key is not provided or found in environment
        requests.exceptions.RequestException: If the API call fails
        Exception: For other API errors
    
    Example:
        >>> response = ask_ai_question(
        ...     input_text="The sky is blue during the day.",
        ...     question_asked="What color is the sky?"
        ... )
        >>> print(response)
        'The sky is blue during the day.'
    """
    # Get API key from parameter or environment
    if api_key is None:
        api_key = os.environ.get("OPENAI_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OpenAI API key must be provided either as a parameter "
            "or via OPENAI_API_KEY environment variable"
        )
    
    # Get model from parameter or environment (with default fallback)
    if model is None:
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
    
    # Get temperature from parameter or environment (with default fallback)
    if temperature is None:
        temp_env = os.environ.get("OPENAI_TEMPERATURE")
        if temp_env:
            try:
                temperature = float(temp_env)
            except ValueError:
                temperature = 0.7  # Fallback if env var is invalid
        else:
            temperature = 0.7
    
    # OpenAI API endpoint
    api_url = "https://api.openai.com/v1/chat/completions"
    
    # Construct the prompt
    system_message = (
        "You are a helpful assistant that answers questions based on the provided context. "
        "Use the context to answer the question accurately and concisely."
    )
    
    user_message = f"""Context:
{input_text}

Question: {question_asked}

Please answer the question based on the context provided above."""
    
    # Prepare request payload
    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        "temperature": temperature
    }
    
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    
    # Prepare headers
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    try:
        # Make the API request
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        # Check for HTTP errors
        response.raise_for_status()
        
        # Parse the response
        response_data = response.json()
        
        # Extract the answer
        if "choices" in response_data and len(response_data["choices"]) > 0:
            answer = response_data["choices"][0]["message"]["content"]
            return answer.strip() if answer else ""
        else:
            raise Exception("Unexpected response format from OpenAI API")
            
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out after {timeout} seconds")
    
    except requests.exceptions.HTTPError as e:
        # Handle HTTP errors with more detail
        try:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", str(e))
            raise Exception(f"OpenAI API error: {error_message}") from e
        except (json.JSONDecodeError, AttributeError):
            raise Exception(f"OpenAI API HTTP error: {str(e)}") from e
    
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to connect to OpenAI API: {str(e)}") from e
    
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise Exception(f"Failed to parse OpenAI API response: {str(e)}") from e
    
    except Exception as e:
        if "OpenAI API" in str(e):
            raise
        raise Exception(f"Unexpected error: {str(e)}") from e

