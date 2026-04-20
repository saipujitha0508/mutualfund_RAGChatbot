"""
HTML Normalizer Module
Cleans and normalizes HTML and PDF content for chunking.
"""
import re
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging

from bs4 import BeautifulSoup, Comment
from PyPDF2 import PdfReader

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HTMLNormalizer:
    """Normalizes HTML content by removing boilerplate and extracting main content."""
    
    def __init__(self, input_dir: str = "data/raw", output_dir: str = "data/normalized"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _remove_boilerplate(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Remove navigation, footers, and other boilerplate elements."""
        # Remove common boilerplate tags
        boilerplate_selectors = [
            'nav', 'footer', 'header',
            '.cookie-banner', '.cookie-notice',
            '.advertisement', '.ad',
            '.popup', '.modal',
            '.social-share', '.social-icons',
            'script', 'style', 'noscript',
            '.navigation', '.menu',
            '.footer-links', '.copyright',
            '[role="navigation"]', '[role="banner"]', '[role="contentinfo"]'
        ]
        
        for selector in boilerplate_selectors:
            for element in soup.select(selector):
                element.decompose()
        
        # Remove HTML comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        return soup
    
    def _clean_whitespace(self, text: str) -> str:
        """Clean up whitespace in text."""
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing whitespace
        text = text.strip()
        return text
    
    def _extract_main_content(self, soup: BeautifulSoup) -> Optional[BeautifulSoup]:
        """Extract the main content from the page."""
        # Try to find main content area
        main_content = (
            soup.find('main') or
            soup.find('article') or
            soup.find('div', class_=re.compile(r'content|main|article', re.I)) or
            soup.find(id=re.compile(r'content|main|article', re.I))
        )
        
        if main_content:
            return main_content
        
        # If no main content found, use body
        return soup.find('body')
    
    def normalize_html(self, html_content: str) -> str:
        """Normalize HTML content."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove boilerplate
        soup = self._remove_boilerplate(soup)
        
        # Extract main content
        main_content = self._extract_main_content(soup)
        if not main_content:
            logger.warning("Could not extract main content")
            return ""
        
        # Get text content with structure
        normalized = str(main_content)
        
        # Clean whitespace
        normalized = self._clean_whitespace(normalized)
        
        return normalized
    
    def process_file(self, filepath: Path) -> Dict:
        """Process a single HTML or PDF file."""
        result = {
            'input_file': str(filepath),
            'status': 'pending',
            'error': None,
            'file_type': 'unknown'
        }
        
        try:
            # Determine file type
            with open(filepath, 'rb') as f:
                header = f.read(4)
                if header == b'%PDF':
                    file_type = 'pdf'
                else:
                    file_type = 'html'
            
            result['file_type'] = file_type
            
            if file_type == 'pdf':
                return self._process_pdf(filepath, result)
            else:
                return self._process_html(filepath, result)
            
        except Exception as e:
            error_msg = f"Error processing {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def _process_pdf(self, filepath: Path, result: Dict) -> Dict:
        """Process a PDF file by extracting text."""
        try:
            logger.info(f"Extracting text from PDF: {filepath}")
            
            with open(filepath, 'rb') as f:
                reader = PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            # Clean up the extracted text
            normalized = self._clean_whitespace(text)
            
            if len(normalized) < 100:
                result.update({
                    'status': 'skipped',
                    'reason': 'Content too short'
                })
                return result
            
            # Save normalized content
            output_filename = f"{filepath.stem}_normalized.txt"
            output_filepath = self.output_dir / output_filename
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(normalized)
            
            result.update({
                'status': 'success',
                'output_file': str(output_filepath),
                'content_length': len(normalized),
                'pages': len(reader.pages)
            })
            
            logger.info(f"Extracted text from PDF {filepath} -> {output_filepath} ({len(normalized)} chars, {len(reader.pages)} pages)")
            
        except Exception as e:
            error_msg = f"Error processing PDF {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def _process_html(self, filepath: Path, result: Dict) -> Dict:
        """Process an HTML file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'lxml')
            soup = self._remove_boilerplate(soup)
            
            # Extract main content
            main_content = soup.find('main') or soup.find('article') or soup.find('body') or soup
            normalized = self._clean_whitespace(main_content.get_text(separator=' '))
            
            if len(normalized) < 100:
                result.update({
                    'status': 'skipped',
                    'reason': 'Content too short'
                })
                return result
            
            # Save normalized content
            output_filename = f"{filepath.stem}_normalized.html"
            output_filepath = self.output_dir / output_filename
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                f.write(normalized)
            
            result.update({
                'status': 'success',
                'output_file': str(output_filepath),
                'content_length': len(normalized)
            })
            
            logger.info(f"Normalized {filepath} -> {output_filepath} ({len(normalized)} chars)")
            
        except Exception as e:
            error_msg = f"Error processing HTML {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def process_all(self) -> Dict:
        """Process all HTML files in the input directory."""
        html_files = list(self.input_dir.glob('*.html'))
        logger.info(f"Found {len(html_files)} HTML files to normalize")
        
        results = []
        for filepath in html_files:
            result = self.process_file(filepath)
            results.append(result)
        
        summary = {
            'total': len(results),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'skipped': sum(1 for r in results if r['status'] == 'skipped'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results
        }
        
        logger.info(f"Normalization complete: {summary['success']}/{summary['total']} successful")
        return summary


def main():
    """CLI to run the normalizer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Normalize HTML content')
    parser.add_argument('--input-dir', default='data/raw', help='Input directory')
    parser.add_argument('--output-dir', default='data/normalized', help='Output directory')
    
    args = parser.parse_args()
    
    normalizer = HTMLNormalizer(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    summary = normalizer.process_all()
    
    print(f"\nNormalization Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Skipped: {summary['skipped']}")
    print(f"  Failed: {summary['failed']}")


if __name__ == "__main__":
    main()
