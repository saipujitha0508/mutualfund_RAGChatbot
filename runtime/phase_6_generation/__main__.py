"""
Phase 6 - Generation
Main entry point for the generation layer.
"""
from .generator import AnswerGenerator

def main():
    """Run the generation service."""
    generator = AnswerGenerator()
    # Test with mock data
    retrieved_chunks = [
        {
            'text': 'The expense ratio is 0.52% for the direct plan.',
            'metadata': {'source_url': 'https://example.com'}
        }
    ]
    result = generator.generate(
        "What is the expense ratio?",
        retrieved_chunks,
        "https://example.com"
    )
    return result

if __name__ == "__main__":
    main()
