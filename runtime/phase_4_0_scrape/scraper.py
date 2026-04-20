"""
Web Scraper Module
Fetches HTML content from allowlisted URLs.
"""
import os
import time
import hashlib
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime
import logging

import requests
from bs4 import BeautifulSoup

from .url_registry import URLRegistry, SourceURL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """Scrapes HTML content from allowlisted URLs."""
    
    def __init__(
        self,
        output_dir: str = "data/raw",
        user_agent: Optional[str] = None,
        delay_between_requests: float = 1.0
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.delay_between_requests = delay_between_requests
        self.registry = URLRegistry()
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    
    def _generate_filename(self, url: str, extension: str = 'html') -> str:
        """Generate a safe filename from URL."""
        url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:12]
        return f"{url_hash}.{extension}"
    
    def _save_html(self, url: str, content: str, fetched_at: str) -> Path:
        """Save HTML content to file."""
        filename = self._generate_filename(url)
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Saved {len(content)} bytes to {filepath}")
        return filepath
    
    def fetch_url(self, source: SourceURL) -> Dict:
        """Fetch a single URL and save its content."""
        result = {
            'source_url': source.source_url,
            'scheme_id': source.scheme_id,
            'doc_type': source.doc_type,
            'status': 'pending',
            'error': None,
            'filepath': None,
            'fetched_at': None,
            'content_hash': None
        }
        
        try:
            logger.info(f"Fetching: {source.source_url}")
            response = self.session.get(
                source.source_url,
                timeout=30,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Verify content type is HTML
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml+xml' not in content_type:
                logger.warning(f"Unexpected content-type for {source.source_url}: {content_type}")
            
            content = response.text
            fetched_at = datetime.utcnow().isoformat() + 'Z'
            
            # Calculate content hash
            content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
            
            # Save to file
            filepath = self._save_html(source.source_url, content, fetched_at)
            
            result.update({
                'status': 'success',
                'filepath': str(filepath),
                'fetched_at': fetched_at,
                'content_hash': content_hash
            })
            
            # Rate limiting
            time.sleep(self.delay_between_requests)
            
        except requests.exceptions.Timeout:
            error_msg = f"Timeout fetching {source.source_url}"
            logger.error(error_msg)
            result.update({'status': 'error', 'error': error_msg})
        
        except requests.exceptions.RequestException as e:
            error_msg = f"Request failed for {source.source_url}: {str(e)}"
            logger.error(error_msg)
            result.update({'status': 'error', 'error': error_msg})
        
        except Exception as e:
            error_msg = f"Unexpected error for {source.source_url}: {str(e)}"
            logger.error(error_msg)
            result.update({'status': 'error', 'error': error_msg})
        
        return result
    
    def scrape_phase_1(self) -> Dict:
        """Scrape all Phase 1 (HTML) URLs."""
        html_sources = self.registry.get_html_urls()
        logger.info(f"Starting Phase 1 scrape for {len(html_sources)} HTML URLs")
        
        results = []
        for source in html_sources:
            result = self.fetch_url(source)
            results.append(result)
        
        summary = {
            'total': len(results),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results
        }
        
        logger.info(f"Phase 1 scrape complete: {summary['success']}/{summary['total']} successful")
        return summary
    
    def scrape_phase_2(self) -> Dict:
        """Scrape all Phase 2 (PDF) URLs."""
        pdf_sources = self.registry.get_pdf_urls()
        logger.info(f"Starting Phase 2 scrape for {len(pdf_sources)} PDF URLs")
        
        results = []
        for source in pdf_sources:
            result = self.fetch_pdf(source)
            results.append(result)
        
        summary = {
            'total': len(results),
            'success': sum(1 for r in results if r['status'] == 'success'),
            'failed': sum(1 for r in results if r['status'] == 'error'),
            'results': results
        }
        
        logger.info(f"Phase 2 scrape complete: {summary['success']}/{summary['total']} successful")
        return summary
    
    def fetch_pdf(self, source: SourceURL) -> Dict:
        """Fetch a single PDF URL and save its content."""
        result = {
            'source_url': source.source_url,
            'scheme_id': source.scheme_id,
            'doc_type': source.doc_type,
            'status': 'pending',
            'error': None,
            'filepath': None,
            'fetched_at': None,
            'content_hash': None
        }
        
        try:
            logger.info(f"Fetching PDF: {source.source_url}")
            response = self.session.get(source.source_url, timeout=30)
            response.raise_for_status()
            
            # Verify it's a PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower():
                logger.warning(f"URL may not be a PDF: {content_type}")
            
            # Generate filename with .pdf extension
            filename = self._generate_filename(source.source_url, 'pdf')
            filepath = self.output_dir / filename
            
            # Save PDF content
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            result.update({
                'status': 'success',
                'filepath': str(filepath),
                'fetched_at': datetime.utcnow().isoformat() + 'Z',
                'content_hash': hashlib.md5(response.content).hexdigest(),
                'size_bytes': len(response.content)
            })
            
            logger.info(f"Saved PDF ({len(response.content)} bytes) to {filepath}")
            
        except Exception as e:
            error_msg = f"Failed to fetch PDF {source.source_url}: {str(e)}"
            logger.error(error_msg)
            result.update({'status': 'error', 'error': error_msg})
        
        return result


def main():
    """CLI to run the scraper."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Scrape URLs from registry')
    parser.add_argument('--phase', type=int, default=1, choices=[1, 2], help='Phase to scrape')
    parser.add_argument('--output-dir', default='data/raw', help='Output directory')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests (seconds)')
    
    args = parser.parse_args()
    
    scraper = WebScraper(
        output_dir=args.output_dir,
        delay_between_requests=args.delay
    )
    
    if args.phase == 1:
        summary = scraper.scrape_phase_1()
    else:
        summary = scraper.scrape_phase_2()
    
    print(f"\nScrape Summary:")
    print(f"  Total: {summary['total']}")
    print(f"  Success: {summary['success']}")
    print(f"  Failed: {summary['failed']}")
    
    if summary['failed'] > 0:
        print("\nFailed URLs:")
        for result in summary['results']:
            if result['status'] == 'error':
                print(f"  - {result['source_url']}: {result['error']}")


if __name__ == "__main__":
    main()
