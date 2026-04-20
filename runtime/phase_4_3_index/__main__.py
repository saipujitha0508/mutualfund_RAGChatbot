"""
Phase 4.3 - Index to Chroma
Main entry point for the Chroma indexing phase.
"""
from dotenv import load_dotenv
from .indexer import ChromaIndexer

def main():
    """Run the Chroma indexing service."""
    load_dotenv()
    indexer = ChromaIndexer()
    summary = indexer.process_all()
    manifest_path = indexer.create_manifest(summary)
    return summary

if __name__ == "__main__":
    main()
