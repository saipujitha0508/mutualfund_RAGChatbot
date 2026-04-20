"""
Safety and Refusal Layer
Routes queries, validates answers, and ensures compliance.
"""
import re
import logging
from typing import Dict, Optional, Tuple
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of queries."""
    FACTUAL = "factual"
    ADVISORY = "advisory"
    COMPARATIVE = "comparative"
    OUT_OF_SCOPE = "out_of_scope"


class SafetyLayer:
    """Handles safety checks, query routing, and refusal handling."""
    
    def __init__(
        self,
        educational_url: str = "https://www.amfiindia.com/investor-education"
    ):
        self.educational_url = educational_url
        
        # Patterns for detecting advisory queries
        self.advisory_patterns = [
            r'should i',
            r'which.*better',
            r'which.*best',
            r'recommend',
            r'advice',
            r'is it good',
            r'is it bad',
            r'worth investing',
            r'should we'
        ]
        
        # Patterns for detecting comparative queries
        self.comparative_patterns = [
            r'compare',
            r'vs\.?',
            r'versus',
            r'better than',
            r'worse than',
            r'outperform',
            r'underperform'
        ]
        
        # PII patterns to detect
        self.pii_patterns = [
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',  # PAN-like
            r'\b\d{12}\b',  # Aadhaar-like
            r'\b\d{10,16}\b',  # Account number-like
            r'\b\d{6}\b',  # OTP-like
        ]
    
    def route_query(self, query: str) -> Tuple[QueryType, Optional[str]]:
        """
        Route query to determine if it should be answered or refused.
        Returns (query_type, reason).
        """
        query_lower = query.lower()
        
        # Check for advisory patterns
        for pattern in self.advisory_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"Query classified as ADVISORY: {query}")
                return QueryType.ADVISORY, "Advisory query detected"
        
        # Check for comparative patterns
        for pattern in self.comparative_patterns:
            if re.search(pattern, query_lower):
                logger.info(f"Query classified as COMPARATIVE: {query}")
                return QueryType.COMPARATIVE, "Comparative query detected"
        
        # Default to factual
        logger.info(f"Query classified as FACTUAL: {query}")
        return QueryType.FACTUAL, None
    
    def check_pii(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check for PII in text.
        Returns (has_pii, detected_pattern).
        """
        for pattern in self.pii_patterns:
            if re.search(pattern, text):
                return True, pattern
        return False, None
    
    def validate_answer(
        self,
        answer: str,
        citation_url: str,
        max_sentences: int = 3
    ) -> Tuple[bool, list]:
        """
        Validate answer against constraints.
        Returns (is_valid, issues).
        """
        issues = []
        
        # Check sentence count
        sentences = re.split(r'[.!?]+', answer)
        sentence_count = len([s for s in sentences if s.strip()])
        if sentence_count > max_sentences:
            issues.append(f"Too many sentences: {sentence_count} (max {max_sentences})")
        
        # Check for exactly one URL
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', answer)
        if len(urls) != 1:
            issues.append(f"Expected exactly 1 URL, found {len(urls)}")
        elif urls[0] != citation_url:
            issues.append(f"Citation URL mismatch")
        
        # Check for forbidden phrases
        forbidden_patterns = [
            r'you should',
            r'should i',
            r'invest in',
            r'better than',
            r'outperform',
            r'guarantee',
            r'recommend',
            r'best fund'
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                issues.append(f"Contains forbidden pattern: {pattern}")
        
        return len(issues) == 0, issues
    
    def generate_refusal(self, query_type: QueryType, reason: str) -> str:
        """Generate a polite refusal response."""
        if query_type == QueryType.ADVISORY:
            return (f"I'm sorry, but I cannot provide investment advice or recommendations. "
                   f"My purpose is to share factual information about mutual fund schemes.\n\n"
                   f"For investment guidance, please consult a SEBI-registered investment advisor.\n\n"
                   f"Learn more: {self.educational_url}")
        
        elif query_type == QueryType.COMPARATIVE:
            return (f"I'm sorry, but I cannot compare funds or recommend which one is better. "
                   f"I can only provide factual information about individual schemes.\n\n"
                   f"For comparative analysis, please consult a SEBI-registered investment advisor.\n\n"
                   f"Learn more: {self.educational_url}")
        
        else:
            return (f"I'm sorry, but I cannot answer this query as it falls outside my scope. "
                   f"I can only provide factual information about mutual fund schemes from official sources.\n\n"
                   f"Learn more: {self.educational_url}")
    
    def should_answer(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Determine if a query should be answered.
        Returns (should_answer, refusal_reason).
        """
        query_type, reason = self.route_query(query)
        
        if query_type == QueryType.FACTUAL:
            return True, None
        else:
            return False, reason


def main():
    """CLI to test the safety layer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Test safety layer')
    parser.add_argument('query', help='Query to test')
    parser.add_argument('--check-answer', help='Answer to validate')
    parser.add_argument('--citation', help='Citation URL for validation')
    
    args = parser.parse_args()
    
    safety = SafetyLayer()
    
    # Test query routing
    should_answer, reason = safety.should_answer(args.query)
    print(f"\nQuery: {args.query}")
    print(f"Should answer: {should_answer}")
    print(f"Reason: {reason}")
    
    if not should_answer:
        query_type, _ = safety.route_query(args.query)
        refusal = safety.generate_refusal(query_type, reason or "")
        print(f"\nRefusal response:\n{refusal}")
    
    # Test answer validation if provided
    if args.check_answer and args.citation:
        is_valid, issues = safety.validate_answer(args.check_answer, args.citation)
        print(f"\nAnswer validation: {is_valid}")
        if issues:
            print("Issues:")
            for issue in issues:
                print(f"  - {issue}")


if __name__ == "__main__":
    main()
