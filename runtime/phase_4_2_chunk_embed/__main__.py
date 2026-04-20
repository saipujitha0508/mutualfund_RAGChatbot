"""
Phase 4.2 - Chunk and Embed
Main entry point for the chunking and embedding phase.
"""
from .chunker import HTMLChunker
from .embedder import ChunkEmbedder
import json
from pathlib import Path

def main():
    """Run the chunking and embedding service."""
    # First, chunk the normalized HTML
    chunker = HTMLChunker()
    url_mapping = chunker._load_url_mapping()
    chunk_summary = chunker.process_all(url_mapping)
    
    # Then, embed the chunks
    embedder = ChunkEmbedder()
    embed_summary = embedder.process_all()
    
    return {
        'chunking': chunk_summary,
        'embedding': embed_summary
    }

if __name__ == "__main__":
    main()
