---
title: FAQ Chatbot API
emoji: 🤖
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# FAQ Chatbot API

RAG-based FAQ assistant for Navi Mutual Fund schemes.

## API Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /threads` - Create a new thread
- `POST /threads/{thread_id}/messages` - Send a message and get AI response
- `GET /threads` - List all threads
- `GET /threads/{thread_id}/messages` - Get messages from a thread
- `DELETE /threads/{thread_id}` - Delete a thread

## Environment Variables

The following environment variables are configured in the Space settings:

- `GROQ_API_KEY` - Groq API key for LLM
- `INGEST_CHROMA_DIR` - Chroma data directory
- `INGEST_CHROMA_COLLECTION` - Chroma collection name
- `PORT` - API port (default: 8000)
- `API_HOST` - API host (default: 0.0.0.0)

## Notes

- This is a runtime API only (does not include ingest pipeline)
- The ingest pipeline runs via GitHub Actions
- Components are lazy-loaded for memory efficiency
