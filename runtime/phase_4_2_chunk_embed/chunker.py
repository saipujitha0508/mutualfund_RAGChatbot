"""
HTML Chunker Module
Chunks normalized HTML content into manageable pieces for embedding.
"""
import re
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import logging

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLChunker:
    """Chunks HTML content into manageable pieces."""
    
    def __init__(
        self,
        input_dir: str = "data/normalized",
        output_dir: str = "data/chunked",
        target_chunk_size: int = 400,
        overlap: float = 0.1
    ):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.target_chunk_size = target_chunk_size
        self.overlap = overlap
    
    def _count_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation: ~4 chars per token)."""
        return len(text) // 4
    
    def _generate_chunk_id(self, content: str, source_url: str, index: int) -> str:
        """Generate a deterministic chunk ID."""
        hash_input = f"{source_url}_{content}_{index}".encode('utf-8')
        return hashlib.md5(hash_input).hexdigest()
    
    def _split_by_headings(self, soup: BeautifulSoup) -> List[BeautifulSoup]:
        """Split HTML by heading tags."""
        sections = []
        current_section = BeautifulSoup('<div></div>', 'lxml').div
        
        for element in soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'table', 'ul', 'ol', 'li']):
            if element.name in ['h1', 'h2', 'h3', 'h4']:
                if current_section.contents:
                    sections.append(current_section)
                current_section = BeautifulSoup('<div></div>', 'lxml').div
            current_section.append(element.copy())
        
        if current_section.contents:
            sections.append(current_section)
        
        return sections
    
    def _split_table_rows(self, table: BeautifulSoup) -> List[str]:
        """Split large tables into row groups."""
        rows = table.find_all('tr')
        if len(rows) <= 10:
            return [str(table)]
        
        # Split into groups of 10 rows with overlap
        groups = []
        for i in range(0, len(rows), 8):
            group = rows[i:i+10]
            table_copy = BeautifulSoup('<table></table>', 'lxml').find('table')
            for row in group:
                table_copy.append(row.copy())
            groups.append(str(table_copy))
        
        return groups
    
    def _extract_text_with_structure(self, soup: BeautifulSoup) -> str:
        """Extract text while preserving some structure."""
        # Get text content
        text = soup.get_text(separator=' ', strip=True)
        return text
    
    def chunk_html(self, html_content: str, source_url: str, metadata: Dict) -> List[Dict]:
        """Chunk HTML content into manageable pieces."""
        soup = BeautifulSoup(html_content, 'lxml')
        chunks = []
        
        # Split by headings
        sections = self._split_by_headings(soup)
        
        chunk_index = 0
        for section in sections:
            # Check if section contains a table
            tables = section.find_all('table')
            
            if tables:
                # Handle tables separately
                for table in tables:
                    table_groups = self._split_table_rows(table)
                    for table_text in table_groups:
                        chunk_text = self._extract_text_with_structure(BeautifulSoup(table_text, 'lxml'))
                        
                        if len(chunk_text) < 50:  # Skip very small chunks
                            continue
                        
                        chunk_id = self._generate_chunk_id(chunk_text, source_url, chunk_index)
                        
                        chunk = {
                            'chunk_id': chunk_id,
                            'text': chunk_text,
                            'source_url': source_url,
                            'chunk_index': chunk_index,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'table',
                                'section_title': section.find(['h1', 'h2', 'h3', 'h4']).get_text().strip() if section.find(['h1', 'h2', 'h3', 'h4']) else None
                            }
                        }
                        chunks.append(chunk)
                        chunk_index += 1
            else:
                # Handle regular text sections
                text = self._extract_text_with_structure(section)
                
                if len(text) < 50:  # Skip very small chunks
                    continue
                
                # Split long sections by token count
                tokens = self._count_tokens(text)
                if tokens > self.target_chunk_size:
                    # Simple sentence-based splitting
                    sentences = re.split(r'(?<=[.!?])\s+', text)
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if self._count_tokens(current_chunk + sentence) < self.target_chunk_size:
                            current_chunk += " " + sentence
                        else:
                            if current_chunk.strip():
                                chunk_id = self._generate_chunk_id(current_chunk, source_url, chunk_index)
                                chunk = {
                                    'chunk_id': chunk_id,
                                    'text': current_chunk.strip(),
                                    'source_url': source_url,
                                    'chunk_index': chunk_index,
                                    'metadata': {
                                        **metadata,
                                        'chunk_type': 'text',
                                        'section_title': section.find(['h1', 'h2', 'h3', 'h4']).get_text().strip() if section.find(['h1', 'h2', 'h3', 'h4']) else None
                                    }
                                }
                                chunks.append(chunk)
                                chunk_index += 1
                            current_chunk = sentence
                    
                    if current_chunk.strip():
                        chunk_id = self._generate_chunk_id(current_chunk, source_url, chunk_index)
                        chunk = {
                            'chunk_id': chunk_id,
                            'text': current_chunk.strip(),
                            'source_url': source_url,
                            'chunk_index': chunk_index,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'text',
                                'section_title': section.find(['h1', 'h2', 'h3', 'h4']).get_text().strip() if section.find(['h1', 'h2', 'h3', 'h4']) else None
                            }
                        }
                        chunks.append(chunk)
                        chunk_index += 1
                else:
                    chunk_id = self._generate_chunk_id(text, source_url, chunk_index)
                    chunk = {
                        'chunk_id': chunk_id,
                        'text': text,
                        'source_url': source_url,
                        'chunk_index': chunk_index,
                        'metadata': {
                            **metadata,
                            'chunk_type': 'text',
                            'section_title': section.find(['h1', 'h2', 'h3', 'h4']).get_text().strip() if section.find(['h1', 'h2', 'h3', 'h4']) else None
                        }
                    }
                    chunks.append(chunk)
                    chunk_index += 1
        
        return chunks
    
    def process_file(self, filepath: Path, source_url: str, metadata: Dict) -> Dict:
        """Process a single normalized HTML file into chunks."""
        result = {
            'input_file': str(filepath),
            'source_url': source_url,
            'status': 'pending',
            'error': None,
            'chunk_count': 0
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Simple text extraction - just get all text
            soup = BeautifulSoup(html_content, 'lxml')
            text = soup.get_text(separator=' ', strip=True)
            
            # Skip if text is too short
            if len(text) < 100:
                logger.warning(f"Text too short in {filepath}: {len(text)} chars")
                result.update({
                    'status': 'success',
                    'chunk_count': 0
                })
                return result
            
            # Split into chunks by sentences
            chunks = []
            chunk_index = 0
            sentences = re.split(r'(?<=[.!?])\s+', text)
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk + sentence) < self.target_chunk_size * 4:
                    current_chunk += " " + sentence
                else:
                    if current_chunk.strip():
                        chunk_id = self._generate_chunk_id(current_chunk, source_url, chunk_index)
                        chunk = {
                            'chunk_id': chunk_id,
                            'text': current_chunk.strip(),
                            'source_url': source_url,
                            'chunk_index': chunk_index,
                            'metadata': {
                                **metadata,
                                'chunk_type': 'text',
                                'section_title': None
                            }
                        }
                        chunks.append(chunk)
                        chunk_index += 1
                    current_chunk = sentence
            
            # Don't forget the last chunk
            if current_chunk.strip():
                chunk_id = self._generate_chunk_id(current_chunk, source_url, chunk_index)
                chunk = {
                    'chunk_id': chunk_id,
                    'text': current_chunk.strip(),
                    'source_url': source_url,
                    'chunk_index': chunk_index,
                    'metadata': {
                        **metadata,
                        'chunk_type': 'text',
                        'section_title': None
                    }
                }
                chunks.append(chunk)
                chunk_index += 1
            
            # Save chunks to file
            output_file = self.output_dir / f"{filepath.stem}_chunks.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(chunks, f, indent=2, ensure_ascii=False)
            
            result.update({
                'status': 'success',
                'output_file': str(output_filepath),
                'chunk_count': len(chunks)
            })
            
            logger.info(f"Chunked {filepath} into {len(chunks)} chunks")
            
        except Exception as e:
            error_msg = f"Error processing {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def process_all(self, url_mapping: Dict = None) -> Dict:
        """Process all normalized HTML and TXT files."""
        html_files = list(self.input_dir.glob('*_normalized.html'))
        txt_files = list(self.input_dir.glob('*_normalized.txt'))
        all_files = html_files + txt_files
        logger.info(f"Found {len(all_files)} normalized files to chunk ({len(html_files)} HTML, {len(txt_files)} TXT)")
        
        # Load URL mapping from sources.csv if not provided
        if url_mapping is None:
            url_mapping = self._load_url_mapping()
        
        results = []
        total_chunks = 0
        
        for filepath in all_files:
            try:
                # Get URL and metadata from mapping
                # Normalized files have "_normalized" suffix, need to remove it
                original_filename = filepath.stem.replace('_normalized', '')
                mapping = url_mapping.get(f"{original_filename}.html", {})
                source_url = mapping.get('source_url')
                metadata = mapping.get('metadata', {})
                
                # If no mapping found, use default
                if not source_url:
                    logger.warning(f"No URL mapping for {filepath.stem}, using default")
                    source_url = "https://www.indmoney.com/mutual-funds/amc/navi-mutual-fund"
                    metadata = {
                        'scheme_id': 'navi_amc',
                        'scheme_name': 'Navi Mutual Fund',
                        'amc': 'Navi Mutual Fund',
                        'doc_type': 'other'
                    }
                
                result = self.process_file(filepath, source_url, metadata)
                results.append(result)
                if result['status'] == 'success':
                    total_chunks += result['chunk_count']
            except Exception as e:
                logger.error(f"Skipping {filepath} due to error: {e}")
                results.append({
                    'input_file': str(filepath),
                    'status': 'error',
                    'error': str(e),
                    'chunk_count': 0
                })
        
        summary = {
            'total': len(results),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'total_chunks': total_chunks,
            'results': results
        }
        
        logger.info(f"Chunking complete: {summary['success']}/{summary['total']} files, {total_chunks} chunks")
        return summary
    
    def _load_url_mapping(self) -> Dict:
        """Load URL mapping from sources.csv by hashing URLs to match filenames."""
        import csv
        import hashlib
        sources_path = Path("data/sources.csv")
        url_mapping = {}
        
        if not sources_path.exists():
            logger.warning(f"sources.csv not found at {sources_path}")
            return url_mapping
        
        with open(sources_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_url = row.get('source_url', '')
                if not source_url:
                    continue
                
                # Generate filename the same way scraper does
                url_hash = hashlib.md5(source_url.encode('utf-8')).hexdigest()[:12]
                filename = f"{url_hash}.html"
                
                url_mapping[filename] = {
                    'source_url': source_url,
                    'metadata': {
                        'scheme_id': row.get('scheme_id', ''),
                        'scheme_name': row.get('scheme_name', ''),
                        'amc': row.get('amc', ''),
                        'doc_type': row.get('doc_type', '')
                    }
                }
        
        logger.info(f"Loaded URL mapping for {len(url_mapping)} files from sources.csv")
        return url_mapping


def main():
    """CLI to run the chunker."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Chunk normalized HTML content')
    parser.add_argument('--input-dir', default='data/normalized', help='Input directory')
    parser.add_argument('--output-dir', default='data/chunked', help='Output directory')
    parser.add_argument('--chunk-size', type=int, default=400, help='Target chunk size (tokens)')
    
    args = parser.parse_args()
    
    chunker = HTMLChunker(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        target_chunk_size=args.chunk_size
    )
    
    # Load URL mapping from sources.csv
    url_mapping = chunker._load_url_mapping()
    summary = chunker.process_all(url_mapping)
    
    print(f"\nChunking Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failed']}")
    print(f"  Total Chunks: {summary['total_chunks']}")


if __name__ == "__main__":
    main()
