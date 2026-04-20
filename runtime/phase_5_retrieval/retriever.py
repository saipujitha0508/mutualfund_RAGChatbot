"""
Retriever Module
Retrieves relevant chunks from local Chroma vector database for user queries.
"""
import os
import logging
from typing import List, Dict, Optional
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VectorRetriever:
    """Retrieves relevant chunks from local Chroma vector database."""
    
    def __init__(
        self,
        collection_name: str = "mf_faq_chunks",
        model_name: str = "BAAI/bge-small-en-v1.5",
        top_k: int = 5
    ):
        self.collection_name = collection_name
        self.top_k = top_k
        self.query_prefix = "Represent this sentence: "
        
        # Initialize local Chroma client
        chroma_dir = Path("data/chroma")
        chroma_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing Chroma local client at {chroma_dir}")
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        
        # Get collection
        try:
            self.collection = self.client.get_collection(name=collection_name)
            logger.info(f"Collection '{collection_name}' loaded with {self.collection.count()} vectors")
        except Exception as e:
            logger.error(f"Failed to load collection: {e}")
            raise
        
        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info("Embedding model loaded")
    
    def _embed_query(self, query: str) -> List[float]:
        """Embed user query using BGE model with query prefix."""
        # Add query prefix for BGE models
        prefixed_query = self.query_prefix + query
        embedding = self.model.encode(
            prefixed_query,
            normalize_embeddings=True
        )
        return embedding.tolist()
    
    def _resolve_scheme(self, query: str, known_schemes: List[str]) -> Optional[str]:
        """Simple scheme resolution from query."""
        query_lower = query.lower()
        for scheme in known_schemes:
            if scheme.lower() in query_lower:
                return scheme
        return None
    
    def retrieve(self, query: str, scheme_filter: Optional[str] = None) -> Dict:
        """Retrieve relevant chunks for a query."""
        logger.info(f"Retrieving for query: {query}")
        
        # Embed query
        query_embedding = self._embed_query(query)
        
        # Build metadata filter if scheme is specified
        where_filter = None
        if scheme_filter:
            where_filter = {"scheme_id": scheme_filter}
        
        # Query Chroma
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=self.top_k,
            where=where_filter
        )
        
        # Format results
        retrieved_chunks = []
        if results['ids'] and results['ids'][0]:
            for i, chunk_id in enumerate(results['ids'][0]):
                chunk = {
                    'chunk_id': chunk_id,
                    'text': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i] if 'distances' in results else None
                }
                retrieved_chunks.append(chunk)
        
        # Select primary citation (highest confidence chunk)
        primary_citation = None
        if retrieved_chunks:
            primary_citation = retrieved_chunks[0]['metadata'].get('source_url')
        
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
        
        return {
            'query': query,
            'retrieved_chunks': retrieved_chunks,
            'primary_citation': primary_citation,
            'chunk_count': len(retrieved_chunks)
        }
    
    def merge_by_source(self, chunks: List[Dict]) -> Dict:
        """Merge chunks from the same source URL."""
        source_groups = {}
        
        for chunk in chunks:
            source_url = chunk['metadata'].get('source_url')
            if source_url not in source_groups:
                source_groups[source_url] = {
                    'source_url': source_url,
                    'chunks': [],
                    'metadata': chunk['metadata']
                }
            source_groups[source_url]['chunks'].append(chunk)
        
        return source_groups


def main():
    """CLI to test the retriever."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Retrieve chunks from Chroma')
    parser.add_argument('query', help='Query to retrieve')
    parser.add_argument('--collection', default='mf_faq_chunks', help='Collection name')
    parser.add_argument('--top-k', type=int, default=20, help='Number of results')
    parser.add_argument('--scheme', help='Filter by scheme ID')
    args = parser.parse_args()
    
    retriever = VectorRetriever(
        collection_name=args.collection,
        top_k=args.top_k
    )
    
    results = retriever.retrieve(args.query, scheme_filter=args.scheme)
    
    print(f"\nRetrieval Results for: {args.query}")
    print(f"Mode: Local")
    print(f"Chunks retrieved: {results['chunk_count']}")
    print(f"Primary citation: {results['primary_citation']}")
    
    print("\nTop chunks:")
    for i, chunk in enumerate(results['retrieved_chunks'][:5], 1):
        print(f"\n{i}. Chunk ID: {chunk['chunk_id']}")
        print(f"   Source: {chunk['metadata'].get('source_url')}")
        print(f"   Distance: {chunk.get('distance', 'N/A')}")
        print(f"   Text: {chunk['text'][:200]}...")


if __name__ == "__main__":
    main()
