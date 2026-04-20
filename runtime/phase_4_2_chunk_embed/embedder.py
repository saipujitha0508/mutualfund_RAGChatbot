"""
Embedder Module
Generates embeddings for chunks using BGE-small-en-v1.5.
"""
import json
from pathlib import Path
from typing import List, Dict
import logging

from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkEmbedder:
    """Generates embeddings for text chunks using BGE-small-en-v1.5."""
    
    def __init__(
        self,
        input_dir: str = "data/chunked",
        output_dir: str = "data/embedded",
        model_name: str = "BAAI/bge-small-en-v1.5",
        batch_size: int = 32
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_name = model_name
        self.batch_size = batch_size
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        logger.info(f"Model loaded. Embedding dimension: {self.model.get_sentence_embedding_dimension()}")
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Generate embeddings for a list of chunks."""
        texts = [chunk['text'] for chunk in chunks]
        
        logger.info(f"Generating embeddings for {len(texts)} chunks...")
        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True,
            normalize_embeddings=True  # L2 normalization for cosine similarity
        )
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk['embedding'] = embeddings[i].tolist()
        
        logger.info(f"Generated {len(embeddings)} embeddings")
        return chunks
    
    def process_file(self, filepath: Path) -> Dict:
        """Process a single chunk JSON file."""
        result = {
            'input_file': str(filepath),
            'output_file': None,
            'status': 'pending',
            'error': None,
            'chunk_count': 0
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            # Generate embeddings
            chunks_with_embeddings = self.embed_chunks(chunks)
            
            # Save embedded chunks
            output_filename = filepath.stem + '_embedded.json'
            output_filepath = self.output_dir / output_filename
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(chunks_with_embeddings, f, indent=2, ensure_ascii=False)
            
            result.update({
                'status': 'success',
                'output_file': str(output_filepath),
                'chunk_count': len(chunks_with_embeddings)
            })
            
            logger.info(f"Embedded {len(chunks_with_embeddings)} chunks from {filepath}")
            
        except Exception as e:
            error_msg = f"Error processing {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def process_all(self) -> Dict:
        """Process all chunk JSON files."""
        chunk_files = list(self.input_dir.glob('*_chunks.json'))
        logger.info(f"Found {len(chunk_files)} chunk files to embed")
        
        results = []
        total_chunks = 0
        
        for filepath in chunk_files:
            result = self.process_file(filepath)
            results.append(result)
            if result['status'] == 'success':
                total_chunks += result['chunk_count']
        
        summary = {
            'model_name': self.model_name,
            'embedding_dimension': self.model.get_sentence_embedding_dimension(),
            'total': len(results),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'total_chunks': total_chunks,
            'results': results
        }
        
        logger.info(f"Embedding complete: {summary['success']}/{summary['total']} files, {total_chunks} chunks")
        return summary


def main():
    """CLI to run the embedder."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate embeddings for chunks')
    parser.add_argument('--input-dir', default='data/chunked', help='Input directory')
    parser.add_argument('--output-dir', default='data/embedded', help='Output directory')
    parser.add_argument('--model', default='BAAI/bge-small-en-v1.5', help='Embedding model')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    
    args = parser.parse_args()
    
    embedder = ChunkEmbedder(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        model_name=args.model,
        batch_size=args.batch_size
    )
    
    summary = embedder.process_all()
    
    print(f"\nEmbedding Summary:")
    print(f"  Model: {summary['model_name']}")
    print(f"  Dimension: {summary['embedding_dimension']}")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total Chunks: {summary['total_chunks']}")


if __name__ == "__main__":
    main()
