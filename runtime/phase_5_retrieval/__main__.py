"""
Phase 5 - Retrieval
Main entry point for the retrieval layer.
"""
from .retriever import VectorRetriever

def main():
    """Run retrieval for a test query."""
    retriever = VectorRetriever()
    results = retriever.retrieve("What is the expense ratio of Navi Midcap 150 fund?")
    return results

if __name__ == "__main__":
    main()
