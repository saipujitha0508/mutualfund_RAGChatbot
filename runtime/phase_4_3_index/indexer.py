"""
Chroma Indexer Module
Indexes embedded chunks into local Chroma vector database.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChromaIndexer:
    """Indexes embedded chunks into local Chroma vector database."""
    
    def __init__(
        self,
        input_dir: str = "data/embedded",
        collection_name: str = "mf_faq_chunks",
        embedding_dimension: int = 384
    ):
        self.input_dir = Path(input_dir)
        self.collection_name = collection_name
        self.embedding_dimension = embedding_dimension
        
        # Initialize local Chroma client
        chroma_dir = Path("data/chroma")
        chroma_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Initializing Chroma local client at {chroma_dir}")
        self.client = chromadb.PersistentClient(path=str(chroma_dir))
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Collection '{self.collection_name}' ready")
    
    def _prepare_batch(self, chunks: List[Dict]) -> Dict:
        """Prepare a batch for Chroma upsert."""
        ids = []
        embeddings = []
        documents = []
        metadatas = []
        
        for chunk in chunks:
            ids.append(chunk['chunk_id'])
            embeddings.append(chunk['embedding'])
            documents.append(chunk['text'])
            
            # Prepare metadata
            metadata = {
                'source_url': chunk['source_url'],
                'chunk_index': chunk['chunk_index'],
                'chunk_type': chunk['metadata'].get('chunk_type', 'unknown'),
            }
            
            # Add optional metadata fields if present
            if 'scheme_id' in chunk['metadata']:
                metadata['scheme_id'] = chunk['metadata']['scheme_id']
            if 'scheme_name' in chunk['metadata']:
                metadata['scheme_name'] = chunk['metadata']['scheme_name']
            if 'amc' in chunk['metadata']:
                metadata['amc'] = chunk['metadata']['amc']
            if 'section_title' in chunk['metadata'] and chunk['metadata']['section_title']:
                metadata['section_title'] = chunk['metadata']['section_title']
            if 'fetched_at' in chunk['metadata']:
                metadata['fetched_at'] = chunk['metadata']['fetched_at']
            
            metadatas.append(metadata)
        
        return {
            'ids': ids,
            'embeddings': embeddings,
            'documents': documents,
            'metadatas': metadatas
        }
    
    def index_chunks(self, chunks: List[Dict]) -> Dict:
        """Index a batch of chunks into Chroma."""
        logger.info(f"Preparing {len(chunks)} chunks for indexing...")
        
        batch = self._prepare_batch(chunks)
        
        # Validate embedding dimensions
        if batch['embeddings']:
            actual_dim = len(batch['embeddings'][0])
            if actual_dim != self.embedding_dimension:
                logger.error(f"Embedding dimension mismatch: expected {self.embedding_dimension}, got {actual_dim}")
                return {
                    'status': 'error',
                    'error': f'Embedding dimension mismatch: expected {self.embedding_dimension}, got {actual_dim}'
                }
        
        logger.info("Upserting chunks to Chroma...")
        self.collection.upsert(
            ids=batch['ids'],
            embeddings=batch['embeddings'],
            documents=batch['documents'],
            metadatas=batch['metadatas']
        )
        
        logger.info(f"Successfully indexed {len(chunks)} chunks")
        return {
            'status': 'success',
            'chunk_count': len(chunks)
        }
    
    def process_file(self, filepath: Path) -> Dict:
        """Process a single embedded chunk JSON file."""
        result = {
            'input_file': str(filepath),
            'status': 'pending',
            'error': None,
            'chunk_count': 0
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            # Index chunks
            index_result = self.index_chunks(chunks)
            
            if index_result['status'] == 'error':
                result.update({
                    'status': 'error',
                    'error': index_result['error']
                })
            else:
                result.update({
                    'status': 'success',
                    'chunk_count': index_result['chunk_count']
                })
            
        except Exception as e:
            error_msg = f"Error processing {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def process_all(self) -> Dict:
        """Process all embedded chunk JSON files."""
        embedded_files = list(self.input_dir.glob('*_embedded.json'))
        logger.info(f"Found {len(embedded_files)} embedded chunk files to index")
        
        results = []
        total_chunks = 0
        
        for filepath in embedded_files:
            result = self.process_file(filepath)
            results.append(result)
            if result['status'] == 'success':
                total_chunks += result['chunk_count']
        
        # Get collection stats
        collection_count = self.collection.count()
        
        summary = {
            'collection_name': self.collection_name,
            'total_files': len(results),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'total_chunks_indexed': total_chunks,
            'collection_count': collection_count,
            'results': results
        }
        
        logger.info(f"Indexing complete: {summary['success']}/{summary['total_files']} files, {total_chunks} chunks")
        logger.info(f"Collection '{self.collection_name}' now has {collection_count} total vectors")
        
        return summary
    
    def create_manifest(self, summary: Dict) -> Path:
        """Create an index manifest file."""
        manifest = {
            'embedding_model_id': 'BAAI/bge-small-en-v1.5',
            'run_id': datetime.utcnow().strftime("%Y%m%d_%H%M%S"),
            'collection_name': self.collection_name,
            'chunk_count': summary['total_chunks_indexed'],
            'collection_count': summary['collection_count'],
            'updated_at': datetime.utcnow().isoformat() + 'Z',
            'indexed_at': datetime.utcnow().isoformat() + 'Z',
            'embedding_dimension': self.embedding_dimension
        }
        
        chroma_dir = Path("data/chroma")
        chroma_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = chroma_dir / 'index_manifest.json'
        
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Index manifest saved to {manifest_path}")
        return manifest_path


def main():
    """CLI to run the Chroma indexer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Index embedded chunks into Chroma')
    parser.add_argument('--input-dir', default='data/embedded', help='Input directory')
    parser.add_argument('--collection', default='mf_faq_chunks', help='Collection name')
    parser.add_argument('--dimension', type=int, default=384, help='Embedding dimension')
    
    args = parser.parse_args()
    
    indexer = ChromaIndexer(
        input_dir=args.input_dir,
        collection_name=args.collection,
        embedding_dimension=args.dimension
    )
    
    summary = indexer.process_all()
    manifest_path = indexer.create_manifest(summary)
    
    print(f"\nIndexing Summary:")
    print(f"  Collection: {summary['collection_name']}")
    print(f"  Mode: Local")
    print(f"  Total Files: {summary['total_files']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Chunks Indexed: {summary['total_chunks_indexed']}")
    print(f"  Collection Count: {summary['collection_count']}")
    print(f"  Manifest: {manifest_path}")


if __name__ == "__main__":
    main()
