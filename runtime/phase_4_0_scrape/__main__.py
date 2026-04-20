"""
Phase 4.0 - Scheduler and Scraping Service
Main entry point for the scraping phase.
"""
import sys
from .scraper import WebScraper

def main():
    """Run the scraping service."""
    # Parse command line arguments for phase
    phase = 1
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg.startswith('--phase='):
                phase = int(arg.split('=')[1])
            elif arg == '--phase' and len(sys.argv) > sys.argv.index(arg) + 1:
                phase = int(sys.argv[sys.argv.index(arg) + 1])
    
    scraper = WebScraper()
    if phase == 2:
        summary = scraper.scrape_phase_2()
    else:
        summary = scraper.scrape_phase_1()
    return summary

if __name__ == "__main__":
    main()
