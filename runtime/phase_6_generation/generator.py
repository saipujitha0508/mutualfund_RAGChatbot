"""
Generator Module
Generates answers using Groq LLM based on retrieved context.
"""
import os
import re
from typing import List, Dict, Optional
from datetime import datetime
import logging

from groq import Groq

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnswerGenerator:
    """Generates answers using Groq LLM with retrieved context."""
    
    def __init__(
        self,
        model_name: str = "llama-3.1-8b-instant",
        max_sentences: int = 3,
        temperature: float = 0.1
    ):
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable is required")
        
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        self.max_sentences = max_sentences
        self.temperature = temperature
    
    def _build_context(self, retrieved_chunks: List[Dict]) -> str:
        """Build context string from retrieved chunks."""
        context_parts = []
        for i, chunk in enumerate(retrieved_chunks, 1):
            source_url = chunk['metadata'].get('source_url', 'Unknown')
            context_parts.append(f"Source URL {i}: {source_url}\n{chunk['text']}")
        
        return "\n\n".join(context_parts)
    
    def _count_sentences(self, text: str) -> int:
        """Count sentences in text."""
        # Simple sentence count based on punctuation
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    def _validate_answer(self, answer: str, citation_url: str) -> Dict:
        """Validate answer against constraints."""
        issues = []
        
        # Check sentence count
        sentence_count = self._count_sentences(answer)
        if sentence_count > self.max_sentences:
            issues.append(f"Too many sentences: {sentence_count} (max {self.max_sentences})")
        
        # Check for exactly one URL
        urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', answer)
        if len(urls) != 1:
            issues.append(f"Expected exactly 1 URL, found {len(urls)}")
        elif urls[0] != citation_url:
            issues.append(f"Citation URL mismatch: expected {citation_url}, got {urls[0]}")
        
        # Check for forbidden phrases
        forbidden_patterns = [
            r'you should',
            r'should i',
            r'invest in',
            r'better than',
            r'outperform',
            r'guarantee',
            r'recommend'
        ]
        
        for pattern in forbidden_patterns:
            if re.search(pattern, answer, re.IGNORECASE):
                issues.append(f"Contains forbidden pattern: {pattern}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'sentence_count': sentence_count
        }
    
    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict],
        citation_url: str,
        fetched_at: Optional[str] = None
    ) -> Dict:
        """Generate answer for a query using retrieved context."""
        if not retrieved_chunks:
            return {
                'status': 'error',
                'error': 'No context available',
                'answer': None
            }
        
        # Build context
        context = self._build_context(retrieved_chunks)
        
        # Format date for footer
        if fetched_at:
            date_str = fetched_at.split('T')[0]
        else:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # System prompt
        system_prompt = f"""You are a facts-only mutual fund FAQ assistant. Your role is to answer factual questions about mutual fund schemes using ONLY the provided context.

STRICT RULES:
1. Answer in at most {self.max_sentences} sentences
2. Include exactly one citation URL from the provided context
3. Do NOT provide investment advice, recommendations, or comparisons
4. Do NOT use phrases like "you should", "invest in", "better than", "outperform", or "guarantee"
5. If the context doesn't contain the answer, say you cannot find it in the indexed sources
6. Always include the footer: "Last updated from sources: {date_str}"

Use ONLY the provided context. Do not add information from outside sources."""
        
        # User prompt
        user_prompt = f"""Question: {query}

CONTEXT:
{context}

Citation URL to use: {citation_url}

Provide a concise, factual answer following the rules above."""
        
        try:
            # Generate response
            logger.info(f"Generating answer for query: {query}")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.temperature,
                max_tokens=300
            )
            
            answer = response.choices[0].message.content.strip()
            
            # Validate answer
            validation = self._validate_answer(answer, citation_url)
            
            if not validation['valid']:
                logger.warning(f"Answer validation failed: {validation['issues']}")
                # Try once more with stricter prompt
                system_prompt_strict = system_prompt + "\n\nCRITICAL: Your previous attempt violated the rules. Be extremely careful to follow ALL rules exactly."
                
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt_strict},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.0,
                    max_tokens=300
                )
                
                answer = response.choices[0].message.content.strip()
                validation = self._validate_answer(answer, citation_url)
            
            logger.info(f"Answer generated successfully")
            
            return {
                'status': 'success',
                'answer': answer,
                'citation_url': citation_url,
                'validation': validation
            }
            
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'answer': None
            }
    
    def generate_fallback(self, citation_url: str, fetched_at: Optional[str] = None) -> str:
        """Generate a safe fallback response."""
        if fetched_at:
            date_str = fetched_at.split('T')[0]
        else:
            date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        return f"I cannot find the specific information in the indexed sources. Please check the official source for more details.\n\nSource: {citation_url}\n\nLast updated from sources: {date_str}"


def main():
    """CLI to test the generator."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate answer using Groq')
    parser.add_argument('query', help='Query to answer')
    parser.add_argument('--context', help='Context text (for testing)')
    parser.add_argument('--citation', help='Citation URL')
    parser.add_argument('--model', default='llama-3.1-8b-instant', help='Groq model')
    
    args = parser.parse_args()
    
    generator = AnswerGenerator(model_name=args.model)
    
    # Mock retrieved chunks for testing
    if args.context:
        retrieved_chunks = [
            {
                'text': args.context,
                'metadata': {'source_url': args.citation or 'https://example.com'}
            }
        ]
    else:
        retrieved_chunks = []
    
    citation_url = args.citation or 'https://example.com'
    
    result = generator.generate(args.query, retrieved_chunks, citation_url)
    
    if result['status'] == 'success':
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nValidation: {result['validation']}")
    else:
        print(f"Error: {result['error']}")


if __name__ == "__main__":
    main()
