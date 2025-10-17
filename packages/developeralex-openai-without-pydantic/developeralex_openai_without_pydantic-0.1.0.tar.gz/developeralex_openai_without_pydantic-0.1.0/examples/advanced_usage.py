"""
Advanced usage example: Custom parameters and error handling
"""

import os
from dotenv import load_dotenv
from openai_wrapper import ask_ai_question

# Load environment variables
load_dotenv()


def example_custom_model():
    """Example using a specific model"""
    print("=" * 60)
    print("Example: Using GPT-4o")
    print("=" * 60)
    
    input_text = """
    Quantum computing uses quantum bits (qubits) which can exist in superposition,
    allowing them to represent both 0 and 1 simultaneously. This property enables
    quantum computers to solve certain problems much faster than classical computers.
    """
    
    question = "What makes quantum computers different from classical computers?"
    
    try:
        response = ask_ai_question(
            input_text=input_text,
            question_asked=question,
            model="gpt-4o",  # Use GPT-4o for more advanced reasoning
            temperature=0.3  # Lower temperature for more factual response
        )
        print(f"Question: {question}")
        print(f"Answer: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_with_token_limit():
    """Example with max_tokens limit"""
    print("=" * 60)
    print("Example: Limiting Response Length")
    print("=" * 60)
    
    input_text = """
    The history of artificial intelligence began in the 1950s. Alan Turing proposed
    the Turing Test in 1950. John McCarthy coined the term "artificial intelligence"
    in 1956. The field has experienced multiple waves of optimism and setbacks,
    known as "AI winters". Recent advances in deep learning have led to breakthrough
    applications in computer vision, natural language processing, and game playing.
    """
    
    question = "Summarize the history of AI in one sentence."
    
    try:
        response = ask_ai_question(
            input_text=input_text,
            question_asked=question,
            max_tokens=50,  # Limit response to ~50 tokens
            temperature=0.5
        )
        print(f"Question: {question}")
        print(f"Answer: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_error_handling():
    """Example demonstrating error handling"""
    print("=" * 60)
    print("Example: Error Handling")
    print("=" * 60)
    
    # Example 1: Invalid API key
    print("Testing with invalid API key...")
    try:
        response = ask_ai_question(
            input_text="Test input",
            question_asked="Test question?",
            api_key="invalid-key-123"
        )
        print(f"Response: {response}")
    except Exception as e:
        print(f"Expected error caught: {type(e).__name__}")
        print(f"Error message: {e}\n")
    
    # Example 2: Empty input
    print("Testing with empty input...")
    try:
        response = ask_ai_question(
            input_text="",
            question_asked="What can you tell me?"
        )
        print(f"Response: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def example_different_temperatures():
    """Example showing effect of different temperatures"""
    print("=" * 60)
    print("Example: Temperature Variations")
    print("=" * 60)
    
    input_text = """
    Mars is the fourth planet from the Sun. It is often called the "Red Planet"
    because of its reddish appearance, caused by iron oxide on its surface.
    """
    
    question = "Why is Mars called the Red Planet?"
    
    temperatures = [0.0, 0.5, 1.0]
    
    for temp in temperatures:
        try:
            print(f"\nTemperature: {temp}")
            response = ask_ai_question(
                input_text=input_text,
                question_asked=question,
                temperature=temp,
                model="gpt-4o-mini"
            )
            print(f"Answer: {response}")
        except Exception as e:
            print(f"Error: {e}")


def example_with_timeout():
    """Example with custom timeout"""
    print("=" * 60)
    print("Example: Custom Timeout")
    print("=" * 60)
    
    input_text = "The speed of light is approximately 299,792,458 meters per second."
    question = "What is the speed of light?"
    
    try:
        response = ask_ai_question(
            input_text=input_text,
            question_asked=question,
            timeout=60  # 60 second timeout instead of default 30
        )
        print(f"Question: {question}")
        print(f"Answer: {response}\n")
    except Exception as e:
        print(f"Error: {e}\n")


def main():
    """Run all advanced examples"""
    print("\n" + "=" * 60)
    print("ADVANCED USAGE EXAMPLES")
    print("=" * 60 + "\n")
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set your API key before running this example.")
        return
    
    # Run examples
    example_custom_model()
    example_with_token_limit()
    example_different_temperatures()
    example_with_timeout()
    example_error_handling()
    
    print("=" * 60)
    print("Examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
