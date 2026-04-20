# Chunking and Embedding Architecture

This document provides detailed implementation guidance for the chunking and embedding phases of the Navi Mutual Fund FAQ Assistant RAG pipeline.

## 1. Overview

The chunking and embedding pipeline transforms raw HTML content from allowlisted sources into indexed vector representations suitable for semantic retrieval. This process is critical for ensuring accurate, context-aware responses to user queries.

## 2. Embedding Model

### 2.1 Model Selection
- **Primary Model:** BAAI/bge-small-en-v1.5
- **Dimensions:** 384
- **Max Input Tokens:** 512
- **Provider:** Local inference via sentence-transformers
- **Rationale:** Lightweight, fast, suitable for small-to-medium corpora (5-20 URLs in Phase 1)

### 2.2 Model Upgrade Path
- **Current:** bge-small-en-v1.5 (384-dim) for 5-20 URLs
- **Future:** bge-base-en-v1.5 (768-dim) for 20+ URLs or when corpus expands to include PDFs
- **Migration Strategy:** Full re-index required when upgrading; document embedding_model_id in manifest

### 2.3 Query Prefix
- **Query Prefix:** "Represent this sentence: "
- **Purpose:** BGE models require this prefix for query embeddings to match document embeddings
- **Implementation:** Prepend this string to user queries before embedding; do NOT prepend to document chunks

## 3. Chunking Strategy

### 3.1 HTML Chunking (Phase 1)

#### 3.1.1 Target Chunk Size
- **Token Range:** 300-450 tokens per chunk
- **Overlap:** 10-15% between consecutive chunks
- **Rationale:** Balances context preservation with retrieval granularity

#### 3.1.2 HTML Parsing Approach
1. **Library:** BeautifulSoup4 (bs4) for HTML parsing
2. **Boilerplate Removal:**
   - Remove: `<nav>`, `<footer>`, `<header>`, cookie banners, ads
   - Keep: Main content sections, tables, scheme details
3. **Section-Based Splitting:**
   - Split on `<h1>`, `<h2>`, `<h3>`, `<h4>` tags
   - Preserve table structure as single units when possible
   - For large tables, split by row groups (e.g., 10-15 rows per chunk)

#### 3.1.3 Table Handling
- **Preserve Integrity:** Keep related table rows together
- **Row Grouping:** For tables with 20+ rows, group by 10-15 rows with overlap
- **Header Retention:** Include table headers in each chunk for context
- **Rationale:** Prevents splitting critical data like expense ratios across chunks

#### 3.1.4 Special Elements
- **Lists:** Keep list items together when contextually related
- **Definitions:** Preserve term-definition pairs
- **Financial Data:** Keep numeric data with its labels (e.g., "Expense Ratio: 0.52%")

### 3.2 PDF Chunking (Phase 2 - Future)

#### 3.2.1 PDF Extraction
- **Library:** PyPDF2 or pdfplumber for text extraction
- **OCR:** Tesseract OCR (only if required and licensed)
- **Fallback:** Document if PDF is image-based and requires OCR

#### 3.2.2 PDF Chunking Rules
- **Page-Aware:** Split by pages first, then by sections within pages
- **Table Detection:** Use pdfplumber's table extraction to preserve table structure
- **Avoid Mid-Table Splits:** Detect table boundaries and avoid splitting within tables
- **Metadata:** Include page number in chunk metadata for citation

## 4. Chunk Metadata Schema

Each chunk must include the following metadata fields:

```python
{
    "chunk_id": str,                    # Deterministic hash of content + source_url
    "source_url": str,                  # Canonical URL (no utm_* params)
    "source_type": str,                 # indmoney_scheme_page, economictimes_factsheet, etc.
    "scheme_id": str | None,            # navi_smallcap250_mq100, navi_midcap150, etc.
    "scheme_name": str | None,          # Human-readable scheme name
    "amc": str,                         # "Navi Mutual Fund"
    "title": str,                       # Page or section title
    "section_title": str | None,        # Specific section within page
    "fetched_at": str,                  # ISO 8601 timestamp
    "content_hash": str,                # Hash of raw content for drift detection
    "chunk_index": int,                 # Position within document (0-based)
    "run_id": str,                      # Ingest run identifier
    "embedding_model_id": str           # "BAAI/bge-small-en-v1.5"
}
```

## 5. Embedding Pipeline

### 5.1 Batch Processing
- **Batch Size:** 32-64 chunks per batch
- **GPU:** Not required for bge-small-en-v1.5 on CPU
- **Memory:** ~500MB RAM for embedding 1000 chunks
- **Timeout:** 30 seconds per batch

### 5.2 Embedding Steps
1. **Load Model:** `SentenceTransformer('BAAI/bge-small-en-v1.5')`
2. **Tokenize:** Convert chunk text to tokens (max 512)
3. **Encode:** Generate 384-dimensional vectors
4. **Normalize:** L2-normalize vectors for cosine similarity
5. **Validate:** Ensure output dimension is 384

### 5.3 Error Handling
- **Oversized Chunks:** Truncate to 512 tokens with warning
- **Empty Chunks:** Skip and log warning
- **Encoding Failures:** Retry once, then skip chunk
- **Validation Failures:** Log chunk_id and content for debugging

## 6. Chroma Integration

### 6.1 Collection Configuration
```python
collection = client.get_or_create_collection(
    name="mf_faq_chunks",
    metadata={"hnsw:space": "cosine"},
    embedding_function=None  # We provide embeddings manually
)
```

### 6.2 Record Shape
```python
{
    "ids": ["chunk_id_1", "chunk_id_2", ...],
    "embeddings": [[0.1, 0.2, ...], [0.3, 0.4, ...], ...],  # 384-dim
    "documents": ["chunk_text_1", "chunk_text_2", ...],
    "metadatas": [
        {
            "source_url": "https://...",
            "scheme_id": "navi_smallcap250_mq100",
            ...
        },
        ...
    ]
}
```

### 6.3 Upsert Strategy
- **Idempotent:** Use deterministic chunk_id for upserts
- **Incremental:** Skip re-embedding if content_hash unchanged
- **Batch Size:** 100 chunks per upsert operation
- **Retry:** 3 retries with exponential backoff on failures

## 7. Implementation Structure

### 7.1 Directory Layout
```
runtime/
├── phase_4_0_scrape/          # Scraping service
│   ├── __init__.py
│   ├── scraper.py
│   └── url_registry.py
├── phase_4_1_normalize/       # HTML normalization
│   ├── __init__.py
│   ├── normalizer.py
│   └── structured_extractor.py
├── phase_4_2_chunk_embed/     # Chunking and embedding
│   ├── __init__.py
│   ├── chunker.py
│   └── embedder.py
└── phase_4_3_index/           # Chroma indexing
    ├── __init__.py
    └── indexer.py
```

### 7.2 CLI Interfaces
```bash
# Scrape URLs
python -m runtime.phase_4_0_scrape

# Normalize HTML
python -m runtime.phase_4_1_normalize

# Chunk and embed
python -m runtime.phase_4_2_chunk_embed

# Index to Chroma
python -m runtime.phase_4_3_index
```

## 8. Quality Assurance

### 8.1 Chunk Validation
- **Minimum Length:** 50 characters (skip shorter)
- **Maximum Length:** 512 tokens (truncate longer)
- **Metadata Completeness:** All required fields present
- **URL Validation:** source_url matches allowlist

### 8.2 Embedding Validation
- **Dimension Check:** All embeddings are 384-dimensional
- **Normalization Check:** L2 norm ≈ 1.0
- **NaN Check:** No NaN values in embeddings
- **Duplicate Check:** No duplicate chunk_ids in batch

### 8.3 Index Validation
- **Count Check:** Chroma count matches chunk count
- **Metadata Check:** All chunks have required metadata
- **Retrieval Test:** Test query returns expected results
- **Citation Check:** Retrieved chunks have valid source_url

## 9. Performance Considerations

### 9.1 Processing Time Estimates
- **Scraping:** ~2-5 seconds per URL (with rate limiting)
- **Normalization:** ~0.5-1 second per page
- **Chunking:** ~0.1-0.5 seconds per page
- **Embedding:** ~0.01-0.05 seconds per chunk (CPU)
- **Indexing:** ~0.1-0.3 seconds per 100 chunks

### 9.2 Storage Estimates
- **Raw HTML:** ~100-500 KB per page
- **Chunks:** ~50-200 chunks per page
- **Embeddings:** ~1.5 KB per chunk (384 * 4 bytes)
- **Total (18 URLs):** ~50-100 MB for full corpus

## 10. Incremental Updates

### 10.1 Change Detection
- **content_hash:** SHA256 of raw HTML content
- **Comparison:** Compare with previous run's manifest
- **Action:** Only re-process changed URLs

### 10.2 Incremental Embedding
```python
if old_content_hash == new_content_hash:
    # Skip: reuse existing embeddings
    pass
else:
    # Re-chunk and re-embed
    new_chunks = chunk_and_embed(new_content)
    # Upsert to Chroma (replaces old chunks)
    chroma_collection.upsert(...)
```

### 10.3 Manifest Tracking
- **File:** `data/structured/<run_id>/manifest.json`
- **Content:** URL → content_hash mapping
- **Purpose:** Enables incremental updates

## 11. Error Recovery

### 11.1 Failed URL Handling
- **Log:** Record URL, error, timestamp
- **Skip:** Continue with other URLs
- **Alert:** Notify operator of persistent failures
- **Retry:** Automatic retry on next scheduled run

### 11.2 Partial Failure Recovery
- **Checkpoint:** Save progress after each phase
- **Resume:** Restart from last successful phase
- **Validation:** Verify data integrity before proceeding

### 11.3 Rollback Strategy
- **Backup:** Keep previous Chroma collection
- **Swap:** Only activate new index after validation
- **Revert:** Restore previous collection on failure

## 12. Monitoring and Logging

### 12.1 Metrics to Track
- **Scrape Success Rate:** URLs successfully fetched
- **Chunk Count:** Total chunks per URL
- **Embedding Time:** Time per batch
- **Index Size:** Total vectors in Chroma
- **Query Latency:** Average retrieval time

### 12.2 Log Levels
- **INFO:** Normal operations, progress updates
- **WARNING:** Skipped chunks, truncated content
- **ERROR:** Failed scrapes, encoding failures
- **DEBUG:** Detailed chunk content, embedding values

## 13. Testing Strategy

### 13.1 Unit Tests
- Test chunking with sample HTML
- Test embedding with known inputs
- Test metadata extraction
- Test Chroma upsert/retrieval

### 13.2 Integration Tests
- End-to-end scrape-to-index pipeline
- Retrieval accuracy with test queries
- Incremental update behavior
- Error handling scenarios

### 13.3 Regression Tests
- Fixed golden set of chunks
- Expected embedding values (or similarity thresholds)
- Citation link validation
- Metadata completeness checks

## 14. Future Enhancements

### 14.1 Advanced Chunking
- Semantic chunking using sentence embeddings
- Dynamic chunk sizing based on content density
- Cross-document chunk merging for related topics

### 14.2 Hybrid Retrieval
- Add BM25/lexical search alongside dense retrieval
- Re-ranking with cross-encoder models
- Query expansion using related terms

### 14.3 Multi-Modal Support
- Image extraction from PDFs
- Chart/table recognition
- OCR for scanned documents

## 15. Summary

This chunking and embedding architecture provides a robust foundation for the Navi Mutual Fund FAQ Assistant. The use of BAAI/bge-small-en-v1.5 ensures efficient local processing, while the structured approach to HTML parsing and table handling preserves critical financial data. The incremental update strategy minimizes processing time for daily refreshes, and comprehensive error handling ensures system reliability.
