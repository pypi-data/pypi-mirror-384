"""
Batch processing example: Process multiple questions efficiently
"""

import os
from dotenv import load_dotenv
from openai_wrapper import ask_ai_question

# Load environment variables
load_dotenv()


def process_multiple_questions():
    """Process multiple questions from the same context"""
    print("=" * 60)
    print("Batch Processing Example")
    print("=" * 60)
    
    # Context about Python
    context = """
    Python is a high-level, interpreted programming language created by Guido van Rossum
    and first released in 1991. It emphasizes code readability with significant indentation.
    Python supports multiple programming paradigms including object-oriented, functional,
    and procedural programming. It has a comprehensive standard library and is widely used
    in web development, data science, artificial intelligence, scientific computing, and
    automation. Python 3, released in 2008, is the current version and is not backwards
    compatible with Python 2.
    """
    
    # List of questions to ask
    questions = [
        "Who created Python?",
        "When was Python first released?",
        "What programming paradigms does Python support?",
        "What is Python commonly used for?",
        "Is Python 3 backwards compatible with Python 2?"
    ]
    
    print(f"\nProcessing {len(questions)} questions about Python...\n")
    
    results = []
    
    for i, question in enumerate(questions, 1):
        try:
            print(f"Question {i}: {question}")
            answer = ask_ai_question(
                input_text=context,
                question_asked=question,
                temperature=0.3  # Lower temperature for factual answers
            )
            print(f"Answer: {answer}\n")
            results.append({
                "question": question,
                "answer": answer,
                "success": True
            })
        except Exception as e:
            print(f"Error: {e}\n")
            results.append({
                "question": question,
                "error": str(e),
                "success": False
            })
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    successful = sum(1 for r in results if r["success"])
    print(f"Processed: {len(questions)} questions")
    print(f"Successful: {successful}")
    print(f"Failed: {len(questions) - successful}")


def process_multiple_documents():
    """Process questions from different documents"""
    print("\n" + "=" * 60)
    print("Multiple Documents Example")
    print("=" * 60)
    
    documents = [
        {
            "title": "Climate Change",
            "content": """
            Climate change refers to long-term shifts in global temperatures and weather
            patterns. While climate change is natural, human activities have been the main
            driver since the 1800s, primarily due to burning fossil fuels like coal, oil,
            and gas, which produce heat-trapping gases.
            """,
            "question": "What is the main cause of recent climate change?"
        },
        {
            "title": "Machine Learning",
            "content": """
            Machine learning is a subset of artificial intelligence that enables systems
            to learn and improve from experience without being explicitly programmed.
            It focuses on developing computer programs that can access data and use it
            to learn for themselves.
            """,
            "question": "How does machine learning differ from traditional programming?"
        },
        {
            "title": "Blockchain",
            "content": """
            Blockchain is a distributed ledger technology that maintains a secure and
            decentralized record of transactions. Each block contains transaction data,
            a timestamp, and a cryptographic hash of the previous block, creating an
            immutable chain.
            """,
            "question": "What makes blockchain secure and immutable?"
        }
    ]
    
    for doc in documents:
        print(f"\nDocument: {doc['title']}")
        print(f"Question: {doc['question']}")
        
        try:
            answer = ask_ai_question(
                input_text=doc['content'],
                question_asked=doc['question'],
                temperature=0.4
            )
            print(f"Answer: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")


def main():
    """Run batch processing examples"""
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set your API key before running this example.")
        return
    
    process_multiple_questions()
    process_multiple_documents()
    
    print("\n" + "=" * 60)
    print("Batch processing completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
