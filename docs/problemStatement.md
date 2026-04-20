# Problem Statement: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
The objective of this project is to build a facts-only FAQ assistant for mutual fund schemes, using Navi Mutual Fund as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources, such as AMC (Asset Management Company) websites, AMFI, and SEBI.

The system must strictly avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link and adhere to defined constraints around clarity, accuracy, and compliance.

## Objective
Design and implement a lightweight Retrieval-Augmented Generation (RAG)-based assistant that:
- Answers factual queries about mutual fund schemes
- Uses a curated corpus of official documents
- Provides concise, source-backed responses

## Target Users
- Retail investors comparing mutual fund schemes
- Customer support and content teams handling repetitive mutual fund queries

## Scope of Work

### 1. Corpus Definition

**AMC (frozen):** Navi Mutual Fund.

**Schemes in corpus (5, direct growth where applicable):**

| Internal `scheme_id` | Scheme (short label) |
|----------------------|----------------------|
| `navi_smallcap250_mq100` | Nifty Smallcap250 Momentum Quality 100 Index Fund |
| `navi_midcap150` | Nifty Midcap 150 Index Fund |
| `navi_large_midcap` | Navi Large & Mid Cap Fund |
| `navi_flexicap` | Navi Flexi Cap Fund |
| `navi_nifty500_multicap_502525` | Nifty 500 Multicap 50:25:25 Index Fund |

**Corpus size:** 18 allowlisted URLs (within the 15–25 document guideline).

**Phase 1 ingestion — HTML only:** The pipeline indexes only HTML pages for the first working RAG. URLs that are PDFs (or ambiguous S3 paths) remain in the registry for citations, compliance, and a later Phase 2 PDF extractor; the fetcher should skip them until PDF ingestion is enabled. Strip tracking query params (e.g. `utm_source`) when storing canonical `source_url` for deduplication and citations.

### 2. FAQ Assistant Requirements
The assistant must:
- Answer facts-only queries, such as:
  - Expense ratio of a scheme
  - Exit load details
  - Minimum SIP amount
  - ELSS lock-in period
  - Riskometer classification
  - Benchmark index
  - Process to download statements or capital gains reports
- Ensure:
  - Each response is limited to a maximum of 3 sentences
  - Each response includes exactly one citation link
  - Each response includes a footer: "Last updated from sources: <date>"

### 3. Refusal Handling
The assistant must refuse non-factual or advisory queries, such as:
- "Should I invest in this fund?"
- "Which fund is better?"

Refusal responses should:
- Be polite and clearly worded
- Reinforce the facts-only limitation
- Provide a relevant educational link (e.g., AMFI or SEBI resource)

### 4. User Interface (Minimal)
The solution should include a simple interface with:
- A welcome message
- Three example questions
- A visible disclaimer: "Facts-only. No investment advice."

## Constraints

### Data and Sources
- Use only official public sources (AMC, AMFI, SEBI)
- Do not use third-party blogs or aggregator websites

### Privacy and Security
- Do not collect, store, or process:
  - PAN or Aadhaar numbers
  - Account numbers
  - OTPs
  - Email addresses or phone numbers

### Content Restrictions
- No investment advice or recommendations
- No performance comparisons or return calculations
- For performance-related queries, provide a link to the official factsheet only

### Transparency
- Responses must be short, factual, and verifiable
- Every answer must include a source link and last updated date

## Expected Deliverables
1. README Document
   - Setup instructions
   - Selected AMC and schemes
   - Architecture overview (RAG approach)
   - Known limitations
2. Disclaimer Snippet
   - "Facts-only. No investment advice."
3. Multiple Chat Thread Support
   - A RAG-based chatbot capable of handling multiple independent conversations or threads simultaneously

## Success Criteria
- Accurate retrieval of factual mutual fund information
- Strict adherence to facts-only responses
- Consistent inclusion of valid source citations
- Proper refusal of advisory queries
- Clean, minimal, and user-friendly interface

## Summary
The goal is to build a trustworthy, transparent, and compliant mutual fund FAQ assistant that prioritizes accuracy over intelligence. The system should ensure that users receive only verified, source-backed financial information, without any advisory bias or speculative content.
