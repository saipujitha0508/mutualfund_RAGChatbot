"""
URL Registry Module
Manages the allowlist of URLs for scraping.
"""
import csv
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse, parse_qs


@dataclass
class SourceURL:
    """Represents a source URL with metadata."""
    source_url: str
    scheme_id: Optional[str]
    doc_type: str
    amc: str
    phase: int  # 1 for HTML, 2 for PDF


class URLRegistry:
    """Manages the URL registry from sources.csv."""
    
    def __init__(self, registry_path: str = "data/sources.csv"):
        self.registry_path = Path(registry_path)
        self.sources: List[SourceURL] = []
        self._load_registry()
    
    def _load_registry(self):
        """Load URLs from the CSV registry."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry file not found: {self.registry_path}")
        
        with open(self.registry_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Strip tracking parameters from URL
                clean_url = self._clean_url(row['source_url'])
                source = SourceURL(
                    source_url=clean_url,
                    scheme_id=row['scheme_id'] if row['scheme_id'] else None,
                    doc_type=row['doc_type'],
                    amc=row['amc'],
                    phase=int(row['phase'])
                )
                self.sources.append(source)
    
    def _clean_url(self, url: str) -> str:
        """Remove tracking parameters from URL."""
        parsed = urlparse(url)
        # Remove utm_* parameters
        query_params = parse_qs(parsed.query)
        clean_params = {
            k: v for k, v in query_params.items() 
            if not k.startswith('utm_')
        }
        # Rebuild URL without tracking params
        clean_query = '&'.join(f"{k}={v[0]}" for k, v in clean_params.items())
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            clean_query,
            ''  # Remove fragment
        ))
    
    def get_phase_urls(self, phase: int) -> List[SourceURL]:
        """Get URLs for a specific phase."""
        return [s for s in self.sources if s.phase == phase]
    
    def get_html_urls(self) -> List[SourceURL]:
        """Get HTML-only URLs (Phase 1)."""
        return self.get_phase_urls(1)
    
    def get_pdf_urls(self) -> List[SourceURL]:
        """Get PDF URLs (Phase 2)."""
        return self.get_phase_urls(2)
    
    def get_scheme_urls(self, scheme_id: str) -> List[SourceURL]:
        """Get URLs for a specific scheme."""
        return [s for s in self.sources if s.scheme_id == scheme_id]
    
    def get_allowlist_hosts(self) -> set:
        """Get set of allowlisted hosts."""
        hosts = set()
        for source in self.sources:
            parsed = urlparse(source.source_url)
            hosts.add(parsed.netloc)
        return hosts
    
    def is_url_allowed(self, url: str) -> bool:
        """Check if a URL is from an allowlisted host."""
        parsed = urlparse(url)
        return parsed.netloc in self.get_allowlist_hosts()


def main():
    """CLI to test URL registry."""
    registry = URLRegistry()
    print(f"Loaded {len(registry.sources)} sources")
    print(f"Allowlisted hosts: {registry.get_allowlist_hosts()}")
    print(f"\nPhase 1 (HTML) URLs: {len(registry.get_html_urls())}")
    print(f"Phase 2 (PDF) URLs: {len(registry.get_pdf_urls())}")
    
    print("\nSample HTML URLs:")
    for source in registry.get_html_urls()[:3]:
        print(f"  - {source.source_url} ({source.scheme_id}, {source.doc_type})")


if __name__ == "__main__":
    main()
