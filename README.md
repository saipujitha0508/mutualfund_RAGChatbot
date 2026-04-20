# Navi Mutual Fund FAQ Assistant

A facts-only RAG-based FAQ assistant for Navi Mutual Fund schemes. This system answers objective, verifiable queries about mutual funds by retrieving information exclusively from official public sources.

## Disclaimer

**Facts-only. No investment advice.** This assistant provides factual information only and does not offer investment recommendations, comparisons, or advice.

## Overview

The assistant uses Retrieval-Augmented Generation (RAG) to answer factual queries about Navi Mutual Fund schemes including:
- Expense ratios
- Exit load details
- Minimum SIP amounts
- Riskometer classifications
- Benchmark indices
- Document availability

### Selected AMC and Schemes

**AMC:** Navi Mutual Fund

**Schemes (5):**
- Nifty Smallcap250 Momentum Quality 100 Index Fund
- Nifty Midcap 150 Index Fund
- Navi Large & Mid Cap Fund
- Navi Flexi Cap Fund
- Nifty 500 Multicap 50:25:25 Index Fund

**Corpus:** 18 allowlisted URLs from IndMoney, Economic Times, Navi, and ET Money

## Architecture

The system follows a closed-book RAG architecture:

1. **Ingestion Pipeline** (Phases 4.0-4.3)
   - Daily scraping from allowlisted URLs (GitHub Actions)
   - HTML normalization and chunking
   - Embedding with BAAI/bge-small-en-v1.5 (local)
   - Vector indexing with Chroma (local storage)

2. **Query Pipeline** (Phases 5-7)
   - Query routing (factual vs advisory detection)
   - Retrieval from Chroma vector store
   - Generation with Groq LLM
   - Safety validation and refusal handling

3. **Multi-Thread Support** (Phase 8)
   - Independent chat sessions
   - Thread history management
   - Context-aware follow-ups

4. **API Layer** (Phase 9)
   - FastAPI REST API
   - Thread management endpoints
   - Health monitoring

5. **Frontend** (Next.js)
   - Dark theme UI
   - Real-time chat interface
   - Example questions

See [docs/rag-architecture.md](docs/rag-architecture.md) for detailed architecture documentation.

## Technology Stack

- **Scheduler:** GitHub Actions (daily cron at 09:15 IST)
- **Vector DB:** Chroma (local persistent storage)
- **Embeddings:** BAAI/bge-small-en-v1.5 (384-dim, local inference)
- **LLM:** Groq API (llama-3.1-8b-instant)
- **Backend:** FastAPI + Python 3.11
- **Frontend:** Next.js 14 + React + TailwindCSS
- **Database:** SQLite (thread storage)

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API key

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd navi-mutual-fund-rag
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export GROQ_API_KEY=your_groq_api_key
```

4. Run the ingest pipeline (build Chroma index):
```bash
python -m runtime.scheduler.local_scheduler
```

5. Start the API server:
```bash
python -m runtime.phase_9_api
```

The API will be available at `http://localhost:8000`

### Frontend Setup

1. Navigate to web directory:
```bash
cd web
```

2. Install dependencies:
```bash
npm install
```

3. Set environment variable:
```bash
export NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

The frontend will be available at `http://localhost:3000`

## Project Structure

```
navi-mutual-fund-rag/
├── docs/                          # Documentation
│   ├── problemStatement.md       # Project problem statement
│   ├── rag-architecture.md       # Detailed RAG architecture
│   ├── chunking-embedding-architecture.md
│   ├── edge-cases.md            # Evaluation edge cases
│   └── deployment-plan.md       # Deployment guide
├── runtime/                      # Backend implementation
│   ├── phase_4_0_scrape/        # Scraping service
│   ├── phase_4_1_normalize/     # HTML normalization
│   ├── phase_4_2_chunk_embed/   # Chunking & embedding
│   ├── phase_4_3_index/         # Chroma indexing
│   ├── phase_5_retrieval/       # Retrieval layer
│   ├── phase_6_generation/      # Generation layer (Groq)
│   ├── phase_7_safety/          # Safety & refusal
│   ├── phase_8_threads/         # Multi-thread support
│   ├── phase_9_api/             # FastAPI application
│   └── scheduler/               # Local scheduler
├── web/                          # Next.js frontend
│   ├── app/                     # Next.js app directory
│   ├── package.json
│   └── README.md
├── data/                         # Data storage
│   ├── sources.csv              # URL registry
│   ├── raw/                     # Scraped HTML
│   ├── normalized/              # Normalized content
│   ├── chunked/                 # Chunks
│   ├── embedded/                # Embedded chunks
│   ├── chroma/                  # Vector index
│   └── structured/              # Structured fund data
├── .github/workflows/           # GitHub Actions
│   └── ingest.yml              # Daily scheduler
├── requirements.txt             # Python dependencies
└── README.md                   # This file
```

## Usage

### Running Individual Phases

```bash
# Scrape URLs
python -m runtime.phase_4_0_scrape

# Normalize HTML
python -m runtime.phase_4_1_normalize

# Chunk and embed
python -m runtime.phase_4_2_chunk_embed

# Index to Chroma
python -m runtime.phase_4_3_index

# Test retrieval
python -m runtime.phase_5_retrieval "What is the expense ratio?"

# Test generation
python -m runtime.phase_6_generation

# Test safety
python -m runtime.phase_7_safety "Should I invest in this fund?"

# Thread management
python -m runtime.phase_8_threads new-thread
python -m runtime.phase_8_threads say --thread-id <id> --message "What is the SIP amount?"

# Start API
python -m runtime.phase_9_api
```

### Running Local Scheduler

To run the complete ingest pipeline locally with logging:

```bash
python -m runtime.scheduler.local_scheduler
```

Logs will be saved to `logs/ingest_<timestamp>.log`

### API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /threads` - Create new thread
- `GET /threads` - List threads
- `GET /threads/{id}/messages` - Get thread messages
- `POST /threads/{id}/messages` - Send message
- `DELETE /threads/{id}` - Delete thread

## Known Limitations

- **Stale Data:** Answers reflect last crawl (daily refresh at 09:15 IST)
- **Narrow Corpus:** Only indexed schemes/pages are answerable
- **HTML Variance:** Sensitive to website layout changes
- **No Real-time Data:** By design, no live market data
- **Router Accuracy:** May misclassify complex queries

## Success Criteria

- Accurate retrieval of factual mutual fund information
- Strict adherence to facts-only responses
- Consistent inclusion of valid source citations
- Proper refusal of advisory queries
- Clean, minimal, and user-friendly interface

## Deployment

See [docs/deployment-plan.md](docs/deployment-plan.md) for detailed deployment instructions.

### Quick Deployment Summary

- **Backend:** Deploy to Render (FastAPI)
- **Frontend:** Deploy to Vercel (Next.js)
- **Scheduler:** GitHub Actions (already configured)

## Evaluation

See [docs/edge-cases.md](docs/edge-cases.md) for comprehensive edge cases and evaluation metrics.

### Key Metrics

- Citation accuracy rate
- Refusal precision/recall
- Sentence compliance (≤ 3 sentences)
- Footer compliance
- Grounding (answer supported by context)

## Contributing

This is a project following the RAG architecture for mutual fund FAQ assistance. For changes:
1. Update relevant documentation
2. Test all phases locally
3. Verify deployment compatibility

## License

This project is for educational and demonstration purposes.

## Contact

For questions about this implementation, refer to the documentation in the `docs/` directory.
