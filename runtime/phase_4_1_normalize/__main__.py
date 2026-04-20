"""
Phase 4.1 - Normalize
Main entry point for the normalization phase.
"""
from .normalizer import HTMLNormalizer

def main():
    """Run the normalization service."""
    normalizer = HTMLNormalizer()
    summary = normalizer.process_all()
    return summary

if __name__ == "__main__":
    main()
