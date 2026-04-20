"""
Structured Data Extractor Module
Extracts structured fund metrics from normalized HTML.
"""
import re
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
import logging

from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StructuredExtractor:
    """Extracts structured fund metrics from HTML content."""
    
    def __init__(self, input_dir: str = "data/normalized", output_dir: str = "data/structured"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create run-specific output directory
        self.run_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        self.run_dir = self.output_dir / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)
    
    def _extract_number(self, text: str) -> Optional[float]:
        """Extract a number from text."""
        match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
        if match:
            try:
                return float(match.group().replace(',', ''))
            except ValueError:
                return None
        return None
    
    def _extract_currency_value(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract currency value from text."""
        # Look for patterns like "₹500", "INR 1000", "Rs. 50"
        patterns = [
            r'(?:₹|INR|Rs\.?)\s*([\d,]+\.?\d*)',
            r'([\d,]+\.?\d*)\s*(?:₹|INR|Rs\.?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    return {
                        'value': value,
                        'currency': 'INR',
                        'raw_text': match.group(0)
                    }
                except ValueError:
                    continue
        return None
    
    def _extract_percentage(self, text: str) -> Optional[float]:
        """Extract percentage from text."""
        match = re.search(r'([\d.]+)\s*%', text)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None
    
    def extract_from_html(self, html_content: str, source_url: str) -> Dict[str, Any]:
        """Extract structured data from HTML content."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        structured_data = {
            'source_url': source_url,
            'fetched_at': datetime.utcnow().isoformat() + 'Z',
            'nav': None,
            'minimum_sip': None,
            'fund_size': None,
            'expense_ratio': None,
            'rating': None,
            'scheme_name': None,
            'amc': 'Navi Mutual Fund',
            'raw_content_hash': None
        }
        
        # Get text content for searching
        text_content = soup.get_text(separator=' ', lower=True)
        
        # Extract NAV
        nav_patterns = [r'nav\s*[:\s]*([\d.]+)', r'net asset value\s*[:\s]*([\d.]+)']
        for pattern in nav_patterns:
            match = re.search(pattern, text_content)
            if match:
                nav_value = self._extract_number(match.group(0))
                if nav_value:
                    structured_data['nav'] = {
                        'value': nav_value,
                        'currency': 'INR'
                    }
                    break
        
        # Extract minimum SIP
        sip_patterns = [r'minimum\s*sip\s*[:\s]*₹?\s*([\d,]+)', r'sip\s*[:\s]*₹?\s*([\d,]+)']
        for pattern in sip_patterns:
            match = re.search(pattern, text_content)
            if match:
                sip_value = self._extract_currency_value(match.group(0))
                if sip_value:
                    structured_data['minimum_sip'] = sip_value
                    break
        
        # Extract fund size / AUM
        aum_patterns = [
            r'fund\s*size\s*[:\s]*₹?\s*([\d,]+)\s*(?:cr|crore)?',
            r'aum\s*[:\s]*₹?\s*([\d,]+)\s*(?:cr|crore)?',
            r'assets\s*under\s*management\s*[:\s]*₹?\s*([\d,]+)\s*(?:cr|crore)?'
        ]
        for pattern in aum_patterns:
            match = re.search(pattern, text_content)
            if match:
                aum_value = self._extract_currency_value(match.group(0))
                if aum_value:
                    structured_data['fund_size'] = aum_value
                    break
        
        # Extract expense ratio
        expense_patterns = [r'expense\s*ratio\s*[:\s]*([\d.]+)\s*%']
        for pattern in expense_patterns:
            match = re.search(pattern, text_content)
            if match:
                expense_value = self._extract_percentage(match.group(0))
                if expense_value:
                    structured_data['expense_ratio'] = {
                        'value': expense_value / 100,  # Convert to decimal
                        'percentage': expense_value
                    }
                    break
        
        # Extract rating/risk
        rating_patterns = [
            r'riskometer\s*[:\s]*(\w+)',
            r'risk\s*level\s*[:\s]*(\w+)',
            r'rating\s*[:\s]*([★\d]+)'
        ]
        for pattern in rating_patterns:
            match = re.search(pattern, text_content)
            if match:
                structured_data['rating'] = match.group(1)
                break
        
        # Extract scheme name from title or h1
        title = soup.find('title')
        if title:
            structured_data['scheme_name'] = title.get_text().strip()
        else:
            h1 = soup.find('h1')
            if h1:
                structured_data['scheme_name'] = h1.get_text().strip()
        
        # Calculate content hash
        structured_data['raw_content_hash'] = hash(html_content)
        
        return structured_data
    
    def process_file(self, filepath: Path, source_url: str) -> Dict:
        """Process a single normalized HTML file."""
        result = {
            'input_file': str(filepath),
            'source_url': source_url,
            'output_file': None,
            'status': 'pending',
            'error': None
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            structured_data = self.extract_from_html(html_content, source_url)
            
            # Save structured data
            output_filename = filepath.stem + '_structured.json'
            output_filepath = self.run_dir / output_filename
            
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(structured_data, f, indent=2, ensure_ascii=False)
            
            result.update({
                'status': 'success',
                'output_file': str(output_filepath)
            })
            
            logger.info(f"Extracted structured data from {filepath}")
            
        except Exception as e:
            error_msg = f"Error processing {filepath}: {str(e)}"
            logger.error(error_msg)
            result.update({
                'status': 'error',
                'error': error_msg
            })
        
        return result
    
    def process_all(self, url_mapping: Dict[str, str]) -> Dict:
        """Process all normalized HTML files with URL mapping."""
        html_files = list(self.input_dir.glob('*_normalized.html'))
        logger.info(f"Found {len(html_files)} normalized HTML files")
        
        results = []
        for filepath in html_files:
            # Get original URL from mapping
            original_filename = filepath.stem.replace('_normalized', '')
            source_url = url_mapping.get(original_filename)
            
            if not source_url:
                logger.warning(f"No URL mapping for {filepath}")
                continue
            
            result = self.process_file(filepath, source_url)
            results.append(result)
        
        # Create manifest
        manifest = {
            'run_id': self.run_id,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_files': len(results),
            'successful': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results
        }
        
        manifest_path = self.run_dir / 'manifest.json'
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info(f"Structured extraction complete: {manifest['successful']}/{manifest['total_files']} successful")
        return manifest


def main():
    """CLI to run the structured extractor."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract structured data from normalized HTML')
    parser.add_argument('--input-dir', default='data/normalized', help='Input directory')
    parser.add_argument('--output-dir', default='data/structured', help='Output directory')
    
    args = parser.parse_args()
    
    extractor = StructuredExtractor(
        input_dir=args.input_dir,
        output_dir=args.output_dir
    )
    
    # For now, use a simple URL mapping (in production, load from scrape results)
    url_mapping = {}
    manifest = extractor.process_all(url_mapping)
    
    print(f"\nStructured Extraction Summary:")
    print(f"  Run ID: {manifest['run_id']}")
    print(f"  Total: {manifest['total_files']}")
    print(f"  Successful: {manifest['successful']}")
    print(f"  Failed: {manifest['failed']}")


if __name__ == "__main__":
    main()
