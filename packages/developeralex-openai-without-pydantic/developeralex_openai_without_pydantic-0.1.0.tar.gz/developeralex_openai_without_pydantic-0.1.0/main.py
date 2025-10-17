"""
Example usage of the OpenAI Wrapper package (without Pydantic)
"""

import os
from dotenv import load_dotenv
from openai_wrapper import ask_ai_question

# Load environment variables from .env file
load_dotenv()


def main():
    """
    Demonstrate the ask_ai_question function
    """
    # Example 1: Simple Q&A
    print("=" * 60)
    print("Example 1: Simple Question Answering")
    print("=" * 60)
    
    input_text = """
    Python is a high-level, interpreted programming language created by Guido van Rossum 
    and first released in 1991. It emphasizes code readability and simplicity. 
    Python supports multiple programming paradigms including procedural, object-oriented, 
    and functional programming.
    """
    
    question = "Who created Python and when was it released?"
    
    try:
        response = ask_ai_question(
            input_text=input_text,
            question_asked=question
        )
        print(f"Question: {question}")
        print(f"Answer: {response}\n")
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set your OPENAI_API_KEY environment variable")
        return
    except Exception as e:
        print(f"API Error: {e}")
        return
    
    # Example 2: Document analysis
    print("=" * 60)
    print("Example 2: Document Analysis")
    print("=" * 60)
    
    input_text = """
    Company Revenue Report 2024:
    - Q1 Revenue: $2.5 million
    - Q2 Revenue: $3.1 million
    - Q3 Revenue: $2.8 million
    - Q4 Revenue: $3.6 million
    Total Annual Revenue: $12.0 million
    Growth Rate: 15% YoY
    """
    
    question = "What was the highest revenue quarter and what was the total annual revenue?"
    
    try:
        response = ask_ai_question(
            input_text=input_text,
            question_asked=question,
            temperature=0.3  # Lower temperature for more factual responses
        )
        print(f"Question: {question}")
        print(f"Answer: {response}\n")
    except Exception as e:
        print(f"API Error: {e}")
    
    # Example 3: Using a different model
    print("=" * 60)
    print("Example 3: Custom Model Selection")
    print("=" * 60)
    
    input_text = """
    Recipe for Chocolate Chip Cookies:
    Ingredients: 2 cups flour, 1 cup butter, 1 cup sugar, 2 eggs, 1 tsp vanilla, 
    2 cups chocolate chips, 1 tsp baking soda, 1/2 tsp salt.
    Instructions: Mix butter and sugar, add eggs and vanilla, combine dry ingredients, 
    fold in chocolate chips, bake at 375°F for 10-12 minutes.
    """
    
    question = "What temperature should I bake these cookies at?"
    
    try:
        response = ask_ai_question(
            input_text=input_text,
            question_asked=question,
            model="gpt-4o-mini",  # Specify model explicitly
            max_tokens=100
        )
        print(f"Question: {question}")
        print(f"Answer: {response}\n")
    except Exception as e:
        print(f"API Error: {e}")


if __name__ == "__main__":
    # Check if API key is set
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  Warning: OPENAI_API_KEY environment variable is not set!")
        print("Please set it before running: export OPENAI_API_KEY='your-key-here'\n")
    
    main()
