# Edge Cases for Evaluation

This document outlines comprehensive edge cases for evaluating the Navi Mutual Fund FAQ Assistant RAG system. These cases cover all components from data ingestion to user interaction.

## 1. Scraping & Ingestion Edge Cases

### 1.1 URL Availability
- **403 Forbidden errors** from sources (e.g., IndMoney blocking)
- **404 Not Found** - URL no longer exists
- **500 Internal Server Error** from source servers
- **503 Service Unavailable** - temporary source downtime
- **Timeout** - source takes too long to respond
- **Redirect loops** - infinite redirect chains
- **Invalid URL format** - malformed URLs in sources.csv
- **URL with tracking parameters** - utm_source, utm_campaign not stripped
- **URL encoding issues** - special characters in URLs (e.g., %3A for colons)
- **Case sensitivity** - URLs with different case but same content

### 1.2 Content Issues
- **Empty response body** - source returns 200 OK but no content
- **Partial content** - truncated HTML due to network issues
- **Malformed HTML** - invalid HTML structure
- **JavaScript-rendered content** - content only loads after JS execution
- **CAPTCHA challenges** - source requires CAPTCHA
- **Rate limiting** - source blocks after too many requests
- **IP blocking** - source IP blocks scraper
- **User-Agent blocking** - source blocks default user agents
- **Content encoding** - gzip, deflate, brotli decompression failures
- **Character encoding** - UTF-8, ASCII, other encoding issues

### 1.3 PDF-Specific Issues
- **PDF download fails** - server returns error
- **Corrupted PDF** - invalid PDF format
- **Password-protected PDF** - encrypted PDF
- **Scanned PDF** - requires OCR
- **Large PDF** - memory issues during extraction
- **PDF with images** - text extraction fails
- **PDF with tables** - table extraction issues
- **PDF with mixed languages** - encoding issues
- **PDF with special fonts** - text extraction failures

### 1.4 Scheduler & Pipeline
- **Scheduler crash** - daily scheduler process dies
- **Missed scheduled run** - scheduler fails to trigger
- **Timezone issues** - IST vs UTC conversion errors
- **Pipeline failure mid-run** - partial ingestion
- **Partial URL failures** - some URLs fail, others succeed
- **Idempotency failure** - re-running causes duplicates
- **Run ID collision** - multiple runs with same ID
- **Disk space exhaustion** - no space for new data
- **Concurrent runs** - multiple pipeline runs overlap
- **Orphaned processes** - child processes don't terminate

### 1.5 Content Hash & Deduplication
- **Hash collision** - different content, same hash
- **Hash algorithm mismatch** - different hash algorithms used
- **Content drift detection failure** - changes not detected
- **False positive drift** - detected change when none exists
- **Duplicate URLs** - same URL listed multiple times
- **Similar URLs** - different URLs, same content

## 2. Normalization Edge Cases

### 2.1 HTML Processing
- **Boilerplate removal failure** - removes important content
- **Boilerplate not removed** - leaves navigation/footer content
- **Table parsing errors** - malformed HTML tables
- **Nested tables** - complex table structures
- **Empty tables** - tables with no data
- **Merged cells** - rowspan/colspan issues
- **Table headers missing** - no header row
- **Dynamic content** - content changes on each load
- **Infinite scroll content** - content not fully loaded
- **Lazy-loaded content** - content loads after scroll

### 2.2 PDF Processing
- **Text extraction failure** - PyPDF2 fails to extract
- **Page boundary issues** - text split across pages
- **OCR required** - scanned images in PDF
- **Multiple columns** - column ordering issues
- **Watermarks** - text obscured by watermarks
- **Headers/footers** - repeated content on each page
- **Page numbers** - page numbers in extracted text
- **Special characters** - symbols not extracted correctly

### 2.3 Content Quality
- **Empty normalized content** - all content stripped
- **Very short content** - single word or phrase
- **Very long content** - exceeds memory limits
- **Special characters** - emojis, symbols, unicode
- **Mixed languages** - English + other languages
- **Typos in source** - source has spelling errors
- **Inconsistent formatting** - varying formats across sources
- **Duplicate sections** - same content repeated
- **Contradictory information** - conflicting facts in same document

## 3. Chunking Edge Cases

### 3.1 Chunk Boundaries
- **Table split mid-row** - table row split across chunks
- **Sentence split mid-sentence** - incomplete sentences
- **Context loss** - important context in previous chunk
- **Overlap miscalculation** - too much or too little overlap
- **Empty chunks** - chunks with no content
- **Single-word chunks** - chunks with one word
- **Very large chunks** - exceed token limits
- **Chunk size variation** - inconsistent chunk sizes
- **Boundary detection failure** - wrong section boundaries

### 3.2 Metadata Loss
- **Source URL missing** - metadata not preserved
- **Scheme ID missing** - cannot identify scheme
- **AMC missing** - cannot identify AMC
- **Fetched_at missing** - no timestamp
- **Content hash missing** - cannot detect drift
- **Title missing** - no section title
- **Doc type missing** - cannot classify document

### 3.3 Duplicate Detection
- **Exact duplicate chunks** - identical content
- **Near-duplicate chunks** - similar but not identical
- **Duplicate chunk IDs** - hash collision
- **Cross-document duplicates** - same content in different sources
- **False positive duplicates** - flagged as duplicate incorrectly

### 3.4 Special Content Types
- **Tables** - tabular data chunking
- **Lists** - numbered/bulleted lists
- **Code blocks** - technical content
- **Formulas** - mathematical expressions
- **Dates** - date formats and parsing
- **Numbers** - numeric values and units
- **Currency** - monetary values
- **Percentages** - percentage values

## 4. Embedding Edge Cases

### 4.1 Model Issues
- **Model loading failure** - model file not found
- **Model version mismatch** - different model versions
- **Dimension mismatch** - wrong embedding dimension
- **Model timeout** - model takes too long
- **OOM error** - out of memory
- **GPU/CPU mismatch** - model expecting GPU on CPU
- **Model corruption** - corrupted model file
- **Unsupported model** - model format not supported

### 4.2 Token Limit
- **Chunk exceeds token limit** - chunk too long
- **Query exceeds token limit** - query too long
- **Batch size too large** - memory issues
- **Batch size too small** - slow processing
- **Truncation** - content cut off
- **Padding issues** - incorrect padding

### 4.3 Embedding Generation
- **Embedding generation failure** - model error
- **Zero embeddings** - all zeros
- **NaN embeddings** - invalid values
- **Embedding drift** - different embeddings for same text
- **Embedding normalization** - normalization issues
- **Batch processing errors** - batch fails partially

## 5. Indexing (Chroma) Edge Cases

### 5.1 Collection Management
- **Collection not found** - collection doesn't exist
- **Collection creation failure** - cannot create collection
- **Collection deletion** - accidental deletion
- **Collection corruption** - corrupted index
- **Multiple collections** - wrong collection selected
- **Collection name collision** - same name in different environments

### 5.2 Upsert Operations
- **Upsert failure** - write operation fails
- **Concurrent upserts** - race conditions
- **Duplicate IDs** - same chunk ID inserted twice
- **ID collision** - different chunks, same ID
- **Metadata size limit** - metadata too large
- **Vector size limit** - vector too large
- **Upsert timeout** - operation times out
- **Partial upsert** - some chunks fail

### 5.3 Query Operations
- **Query failure** - read operation fails
- **Empty results** - no chunks found
- **Too many results** - performance issues
- **Filter failure** - metadata filter fails
- **Invalid filter** - malformed filter query
- **Filter mismatch** - no matches for filter
- **Distance calculation error** - similarity score issues
- **N_results too large** - too many results requested

### 5.4 Storage Issues
- **Disk space full** - no space for vectors
- **File permission errors** - cannot read/write
- **File locking** - file locked by another process
- **Network storage issues** - NFS/SMB problems
- **Corrupted files** - index files corrupted
- **Version mismatch** - Chroma version incompatibility
- **PersistentClient path issues** - wrong path specified

## 6. Retrieval Edge Cases

### 6.1 Query Processing
- **Empty query** - user sends empty string
- **Very short query** - single word
- **Very long query** - exceeds limits
- **Special characters** - emojis, symbols
- **Mixed languages** - English + other languages
- **Typos** - spelling errors in query
- **Ambiguous scheme names** - similar scheme names
- **Unknown scheme** - scheme not in corpus
- **Multiple schemes in query** - querying multiple schemes
- **Out-of-scope query** - query not about mutual funds

### 6.2 Retrieval Results
- **No relevant chunks** - no chunks match query
- **Low similarity scores** - all chunks have low scores
- **All chunks from same source** - lack of diversity
- **Conflicting information** - chunks disagree
- **Stale information** - old data retrieved
- **Wrong scheme retrieved** - retrieved wrong scheme
- **Generic chunks** - too general information
- **Missing key information** - specific fact not found
- **Too many chunks** - overwhelming context
- **Too few chunks** - insufficient context

### 6.3 Source Selection
- **Multiple high-scoring chunks** - which to cite?
- **Tie-breaking** - equal scores
- **Conflict resolution** - chunks disagree
- **Citation URL missing** - no URL in metadata
- **Citation URL invalid** - malformed URL
- **Citation URL not allowlisted** - unauthorized source
- **Citation URL changed** - URL changed since scrape
- **Citation URL duplicate** - same URL for different content

### 6.4 Performance-Related Queries
- **Return queries** - "what are the returns?"
- **Performance comparison** - "which performed better?"
- **Future predictions** - "what will the returns be?"
- **Past performance** - historical return queries
- **Benchmark comparison** - "vs benchmark"
- **Risk-return queries** - risk-adjusted returns

## 7. Generation (LLM) Edge Cases

### 7.1 API Issues
- **API key missing** - no GROQ_API_KEY
- **API key invalid** - wrong key
- **API key expired** - key no longer valid
- **Rate limiting** - API rate limit exceeded
- **API timeout** - request times out
- **API unavailable** - service down
- **Model unavailable** - specified model not available
- **Quota exceeded** - API quota exceeded
- **Billing issue** - payment required
- **Network issues** - cannot reach API

### 7.2 Response Generation
- **Exceeds sentence limit** - more than 3 sentences
- **Missing citation** - no URL in response
- **Multiple citations** - more than one URL
- **Wrong citation** - incorrect URL
- **Invalid citation** - malformed URL
- **Investment advice** - "you should invest"
- **Comparison language** - "better than", "best"
- **Guarantees** - "guaranteed returns"
- **Recommendations** - "I recommend"
- **Opinion** - subjective statements
- **Hallucination** - invented facts
- **Incomplete response** - doesn't answer query
- **Irrelevant response** - answers different question
- **Too generic** - vague response
- **Too specific** - overly detailed
- **Missing footer** - no "Last updated" line
- **Wrong footer date** - incorrect date
- **Empty response** - no content

### 7.3 Prompt Engineering
- **Context too long** - exceeds model context window
- **Context too short** - insufficient information
- **Conflicting context** - contradictory information
- **System prompt failure** - instructions not followed
- **Few-shot examples** - examples not working
- **Temperature issues** - too random or too deterministic
- **Token limit** - response cut off mid-sentence
- **Format issues** - JSON/structured output failures

## 8. Safety & Refusal Edge Cases

### 8.1 Advisory Query Detection
- **False positive** - factual query flagged as advisory
- **False negative** - advisory query not detected
- **Edge cases** - borderline queries
- **Implicit advice** - subtle advisory language
- **Personal situation** - "I am 45 years old..."
- **Comparative queries** - "which is better?"
- **Recommendation queries** - "should I invest?"
- **Ranking queries** - "best fund for..."
- **Timing queries** - "when should I invest?"

### 8.2 Refusal Responses
- **Too harsh** - rude refusal
- **Too vague** - unclear refusal
- **Missing educational link** - no AMFI/SEBI link
- **Wrong educational link** - invalid link
- **Educational link broken** - 404 error
- **Refusal tone inconsistent** - varies between refusals
- **Refusal missing** - answers advisory query
- **Refusal too long** - exceeds sentence limit

### 8.3 PII Detection
- **PAN numbers** - personal account numbers
- **Aadhaar numbers** - Indian ID numbers
- **Account numbers** - bank account details
- **OTP codes** - one-time passwords
- **Email addresses** - personal emails
- **Phone numbers** - contact numbers
- **Addresses** - physical addresses
- **False positives** - non-PII flagged as PII
- **False negatives** - PII not detected

### 8.4 Performance Query Handling
- **Return queries not redirected** - answers returns directly
- **Performance comparison** - compares funds
- **Future predictions** - predicts future returns
- **Missing factsheet link** - no link provided
- **Wrong factsheet link** - incorrect link
- **Generic refusal** - refuses all performance queries

## 9. Multi-Thread Chat Edge Cases

### 9.1 Thread Management
- **Thread ID collision** - duplicate thread IDs
- **Thread creation failure** - cannot create thread
- **Thread deletion failure** - cannot delete thread
- **Thread not found** - invalid thread ID
- **Thread list overflow** - too many threads
- **Thread metadata corruption** - corrupted thread data
- **Orphaned threads** - threads without messages
- **Zombie threads** - threads marked active but inactive

### 9.2 Message Management
- **Message loss** - messages not persisted
- **Message duplication** - same message added twice
- **Message ordering** - wrong order
- **Message corruption** - corrupted message content
- **Empty messages** - messages with no content
- **Very long messages** - exceed limits
- **Special characters** - emojis, symbols
- **Message timestamp issues** - wrong timestamps
- **Role confusion** - wrong role assigned

### 9.3 Context Window
- **History overflow** - too many messages
- **History truncation** - wrong messages truncated
- **Empty history** - no previous messages
- **Context window mismatch** - different sizes
- **Memory leak** - memory grows with history
- **Context injection** - wrong context from other threads

### 9.4 Concurrency
- **Concurrent writes** - race conditions
- **Cross-thread bleeding** - context from other threads
- **Session key conflicts** - same session key for different threads
- **Lock contention** - database locks
- **Deadlock** - threads waiting on each other
- **Connection pool exhaustion** - no available DB connections
- **Transaction conflicts** - concurrent modifications

### 9.5 Privacy & Security
- **Session hijacking** - unauthorized access to thread
- **Thread ID guessing** - predictable thread IDs
- **Message interception** - messages read by wrong user
- **Data leak** - sensitive data in logs
- **SQL injection** - malicious queries
- **XSS** - cross-site scripting in UI

## 10. API Layer Edge Cases

### 10.1 Request Handling
- **Invalid JSON** - malformed request body
- **Missing required fields** - required fields absent
- **Invalid field types** - wrong data types
- **Field validation errors** - validation failures
- **Empty request body** - no data sent
- **Very large request body** - exceeds limits
- **Malformed URLs** - invalid endpoint URLs
- **HTTP method mismatch** - wrong method used

### 10.2 Response Handling
- **Invalid response format** - wrong format
- **Missing response fields** - fields absent
- **Null values** - unexpected nulls
- **Empty response** - no data returned
- **Very large response** - exceeds limits
- **Serialization errors** - JSON serialization failures
- **Encoding issues** - character encoding problems

### 10.3 Authentication & Authorization
- **Missing auth token** - no token provided
- **Invalid auth token** - wrong token
- **Expired auth token** - token expired
- **Admin endpoint access** - unauthorized access
- **CORS issues** - cross-origin request blocked
- **CSRF issues** - cross-site request forgery
- **Rate limiting** - too many requests

### 10.4 Health & Monitoring
- **Health check failure** - service unhealthy
- **Slow response time** - performance degradation
- **High memory usage** - memory leak
- **High CPU usage** - CPU spike
- **Database connection failure** - cannot connect to DB
- **Chroma connection failure** - cannot connect to Chroma
- **LLM API failure** - cannot reach LLM

## 11. Data Quality Edge Cases

### 11.1 Stale Data
- **Data not refreshed** - scheduler missed run
- **Content drift** - source changed, not detected
- **Old fetched_at** - stale timestamp
- **Inconsistent refresh** - some sources updated, others not
- **Partial refresh** - only some URLs refreshed
- **Refresh failure** - refresh process failed

### 11.2 Registry Issues
- **Duplicate URLs** - same URL listed multiple times
- **Invalid URLs** - malformed URLs
- **Dead URLs** - URLs that no longer exist
- **Redirected URLs** - URLs that redirect
- **URL scheme mismatch** - http vs https
- **Missing scheme_id** - no scheme identifier
- **Invalid scheme_id** - wrong scheme ID
- **Missing doc_type** - no document type
- **Invalid doc_type** - wrong document type

### 11.3 Metadata Issues
- **Missing metadata** - required fields absent
- **Invalid metadata** - wrong data types
- **Corrupted metadata** - corrupted data
- **Inconsistent metadata** - conflicting values
- **Outdated metadata** - old values
- **Missing source_url** - no URL in metadata
- **Missing fetched_at** - no timestamp
- **Missing scheme_id** - no scheme identifier

## 12. Performance Edge Cases

### 12.1 Latency Issues
- **Slow retrieval** - Chroma query takes too long
- **Slow generation** - LLM response takes too long
- **Slow embedding** - embedding generation slow
- **Slow scraping** - source response slow
- **Slow normalization** - processing slow
- **Slow chunking** - chunking slow
- **Slow indexing** - Chroma upsert slow

### 12.2 Resource Issues
- **High memory usage** - memory leak
- **High CPU usage** - CPU spike
- **High disk usage** - disk space exhausted
- **High network usage** - bandwidth saturation
- **Connection pool exhaustion** - no available connections
- **File handle exhaustion** - too many open files
- **Thread pool exhaustion** - no available threads

### 12.3 Scalability Issues
- **Concurrent request handling** - too many simultaneous requests
- **Database bottleneck** - DB cannot handle load
- **Chroma bottleneck** - vector DB cannot handle load
- **LLM API bottleneck** - API rate limits
- **Network bottleneck** - network saturation
- **Load balancing issues** - uneven distribution

## 13. Security Edge Cases

### 13.1 Input Validation
- **SQL injection** - malicious SQL in input
- **XSS** - malicious scripts in input
- **Command injection** - malicious commands
- **Path traversal** - directory traversal attacks
- **Buffer overflow** - input too large
- **Format string attacks** - format string vulnerabilities

### 13.2 Authentication & Authorization
- **Weak passwords** - weak admin passwords
- **Password reuse** - same password for multiple accounts
- **Session fixation** - session hijacking
- **Session timeout** - sessions don't expire
- **Privilege escalation** - unauthorized privilege increase
- **Token leakage** - tokens exposed in logs

### 13.3 Data Security
- **PII in logs** - sensitive data in logs
- **API key exposure** - keys in logs or code
- **Unencrypted storage** - sensitive data unencrypted
- **Unencrypted transmission** - data sent in plain text
- **Weak encryption** - weak encryption algorithms
- **Key management** - poor key handling

### 13.4 Infrastructure Security
- **Outdated dependencies** - vulnerable packages
- **Missing security headers** - no security headers
- **CORS misconfiguration** - overly permissive CORS
- **HTTPS not enforced** - HTTP allowed
- **Missing rate limiting** - no rate limiting
- **DDoS vulnerability** - vulnerable to DDoS

## 14. Integration Edge Cases

### 14.1 Dependency Issues
- **Missing dependencies** - required packages not installed
- **Version conflicts** - incompatible package versions
- **Dependency updates** - breaking changes in updates
- **Transitive dependencies** - issues in indirect dependencies
- **Circular dependencies** - dependency cycles
- **Orphaned dependencies** - unused dependencies

### 14.2 Environment Issues
- **Missing environment variables** - required env vars absent
- **Invalid environment variables** - wrong values
- **Environment mismatch** - dev vs prod differences
- **Configuration errors** - wrong configuration
- **File permission issues** - cannot read/write files
- **Path issues** - wrong file paths
- **Working directory issues** - wrong working directory

### 14.3 External Service Integration
- **Chroma Cloud fallback** - attempts to use Chroma Cloud (should not)
- **LLM provider changes** - API changes
- **Source website changes** - website structure changes
- **AMFI/SEBI link changes** - educational links broken
- **CDN issues** - CDN unavailability
- **Third-party API changes** - API breaking changes

## 15. User Experience Edge Cases

### 15.1 UI Issues
- **Empty state** - no threads or messages
- **Loading state** - long loading times
- **Error state** - errors not handled gracefully
- **Responsive design** - issues on mobile devices
- **Browser compatibility** - issues on certain browsers
- **Accessibility** - screen reader issues
- **Keyboard navigation** - keyboard shortcuts not working
- **Dark mode** - issues with dark mode

### 15.2 Interaction Issues
- **Double submission** - form submitted twice
- **Back button** - issues with browser back
- **Refresh** - page refresh causes issues
- **Network interruption** - connection lost during operation
- **Tab switching** - issues with multiple tabs
- **Session timeout** - user session expires
- **Logout issues** - logout doesn't work properly

### 15.3 Content Issues
- **Disclaimer visibility** - disclaimer not visible
- **Example questions** - example questions not working
- **Welcome message** - welcome message issues
- **Error messages** - unclear error messages
- **Success messages** - missing success feedback
- **Loading indicators** - no loading feedback
- **Empty results** - no results shown

## 16. Testing & Evaluation Edge Cases

### 16.1 Test Data
- **Golden set coverage** - test cases don't cover all scenarios
- **Stale golden set** - test cases outdated
- **Ambiguous test cases** - unclear expected behavior
- **Conflicting test cases** - contradictory expectations
- **Missing edge cases** - edge cases not tested
- **Performance test issues** - unrealistic test scenarios

### 16.2 Evaluation Metrics
- **Citation accuracy** - wrong citations scored correctly
- **Grounding issues** - hallucinations not detected
- **Refusal precision** - refusals measured incorrectly
- **False positives** - correct answers flagged as wrong
- **False negatives** - wrong answers flagged as correct
- **Metric calculation errors** - wrong formulae

### 16.3 Regression Testing
- **Regression not detected** - bugs not caught
- **False regression** - non-issues flagged as regressions
- **Test flakiness** - tests fail intermittently
- **Test timeout** - tests take too long
- **Test environment issues** - environment differences cause failures

## 17. Disaster Recovery Edge Cases

### 17.1 Backup & Restore
- **Backup failure** - backup not created
- **Backup corruption** - backup corrupted
- **Restore failure** - cannot restore from backup
- **Point-in-time recovery** - cannot restore to specific point
- **Incremental backup issues** - incremental backup failures
- **Backup verification** - backup not verified

### 17.2 Failover
- **Primary failure** - primary system fails
- **Failover delay** - failover takes too long
- **Failback issues** - cannot fail back
- **Split-brain** - multiple primaries active
- **Data inconsistency** - data inconsistent after failover
- **State loss** - state lost during failover

### 17.3 Data Loss
- **Accidental deletion** - data deleted by mistake
- **Corruption** - data corrupted
- **Ransomware** - data encrypted by malware
- **Hardware failure** - disk failure
- **Natural disaster** - physical damage
- **Human error** - operator mistakes

## 18. Compliance & Regulatory Edge Cases

### 18.1 SEBI Compliance
- **Investment advice** - violates SEBI regulations
- **Performance claims** - misleading performance data
- **Risk disclosure** - inadequate risk information
- **Past performance** - improper use of past performance
- **Disclaimer adequacy** - disclaimer not sufficient
- **Record keeping** - records not maintained properly

### 18.2 Data Privacy
- **GDPR compliance** - personal data handling
- **Data retention** - data kept too long
- **Data deletion** - right to be forgotten
- **Data portability** - data export issues
- **Consent management** - consent not obtained
- **Privacy policy** - privacy policy issues

### 18.3 Financial Regulations
- **AMFI compliance** - AMFI guidelines
- **RBI compliance** - RBI regulations
- **Tax implications** - incorrect tax information
- **KYC requirements** - KYC issues
- **AML compliance** - anti-money laundering
- **Reporting requirements** - regulatory reporting

## Summary

This comprehensive edge case document covers 18 major categories with over 300 specific edge cases for the Mutual Fund FAQ Assistant RAG system. Each category should be tested systematically to ensure system robustness, reliability, and compliance.

### Priority Categories

**High Priority:**
- Scraping failures (403, 404, timeouts)
- Investment advice in responses
- Missing citations
- PII handling
- Data staleness
- Refusal detection

**Medium Priority:**
- Chunking boundary issues
- Retrieval accuracy
- Response length limits
- Multi-thread isolation
- Performance queries

**Low Priority:**
- UI responsiveness
- Browser compatibility
- Accessibility
- Minor formatting issues

### Evaluation Metrics

### Success Metrics
- **Citation Accuracy:** % of answers with valid allowlist URLs
- **Refusal Precision:** % of advisory queries correctly refused
- **Refusal Recall:** % of refused queries that should be refused
- **Sentence Compliance:** % of answers ≤ 3 sentences
- **Footer Compliance:** % of answers with required footer
- **Retrieval Accuracy:** % of queries with relevant chunks
- **Grounding:** % of answers supported by retrieved context

### Failure Metrics
- **False Positives:** Factual queries incorrectly refused
- **False Negatives:** Advisory queries incorrectly answered
- **Citation Errors:** Invalid or missing citations
- **Sentence Violations:** Answers exceeding 3 sentences
- **Hallucinations:** Answers not supported by retrieved context
- **PII Leaks:** Sensitive data exposed in responses or logs
- **Data Staleness:** Answers using outdated information
