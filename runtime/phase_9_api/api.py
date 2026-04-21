"""
FastAPI Application
REST API for the Mutual Fund FAQ Assistant.
"""
import os
from typing import Optional, List
from datetime import datetime
import logging
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Load environment variables
load_dotenv()

# Import phase modules
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from phase_5_retrieval.retriever import VectorRetriever
from phase_6_generation.generator import AnswerGenerator
from phase_7_safety.safety import SafetyLayer
from phase_8_threads.threads import ThreadManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FAQ Chatbot API",
    description="Facts-only RAG-based FAQ assistant for Navi Mutual Fund schemes",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Initialize components (lazy loading for memory efficiency)
retriever = None
generator = None
safety = None
thread_manager = None

DEBUG_MODE = os.getenv("RUNTIME_API_DEBUG", "0") == "1"
_components_initialized = False


def ensure_components_initialized():
    """Initialize components on first use (lazy loading for Render 512MB limit)."""
    global retriever, generator, safety, thread_manager, _components_initialized
    
    if _components_initialized:
        return
    
    logger.info("Lazy loading components...")
    
    try:
        retriever = VectorRetriever()
        logger.info("Retriever initialized (Local Chroma)")
    except Exception as e:
        logger.error(f"Failed to initialize retriever: {e}")
    
    if GENERATION_ENABLED:
        try:
            generator = AnswerGenerator()
            logger.info("Generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize generator: {e}")
    else:
        logger.info("Generator initialization skipped (GROQ_API_KEY not set)")
    
    try:
        safety = SafetyLayer()
        logger.info("Safety layer initialized")
    except Exception as e:
        logger.error(f"Failed to initialize safety layer: {e}")
    
    try:
        thread_manager = ThreadManager()
        logger.info("Thread manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize thread manager: {e}")
    
    _components_initialized = True
    logger.info("Components lazy loaded successfully")

# Check for required environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY or GROQ_API_KEY == "your_groq_api_key_here":
    logger.warning("GROQ_API_KEY not set or is placeholder. Generation features will be disabled.")
    GENERATION_ENABLED = False
else:
    GENERATION_ENABLED = True


class Message(BaseModel):
    """Message model."""
    role: str
    content: str


class CreateThreadRequest(BaseModel):
    """Request to create a new thread."""
    session_key: Optional[str] = None

    class Config:
        extra = "allow"


class SendMessageRequest(BaseModel):
    """Request to send a message to a thread."""
    content: str


class ThreadResponse(BaseModel):
    """Thread response."""
    thread_id: str
    session_key: Optional[str]
    created_at: str
    updated_at: str


class MessageResponse(BaseModel):
    """Message response."""
    id: int
    role: str
    content: str
    timestamp: str


class ChatResponse(BaseModel):
    """Chat response."""
    answer: str
    citation_url: Optional[str]
    thread_id: str
    debug: Optional[dict] = None


@app.on_event("startup")
async def startup_event():
    """Initialize lightweight components on startup (heavy components loaded lazily)."""
    logger.info("API startup complete (heavy components will be lazy loaded on first request)")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Navi Mutual Fund FAQ Assistant API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "disclaimer": "Facts-only. No investment advice."
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "components": {
            "retriever": retriever is not None,
            "generator": generator is not None,
            "safety": safety is not None,
            "thread_manager": thread_manager is not None
        }
    }


@app.post("/threads", response_model=ThreadResponse)
async def create_thread(request: Optional[CreateThreadRequest] = None):
    """Create a new chat thread."""
    ensure_components_initialized()
    if not thread_manager:
        raise HTTPException(status_code=503, detail="Thread manager not available")
    
    session_key = request.session_key if request else None
    thread_id = thread_manager.create_thread(session_key=session_key)
    thread = thread_manager.list_threads(limit=1)[0]
    
    return ThreadResponse(**thread)


@app.get("/threads")
async def list_threads(limit: int = 50):
    """List all threads."""
    ensure_components_initialized()
    if not thread_manager:
        raise HTTPException(status_code=503, detail="Thread manager not available")
    
    threads = thread_manager.list_threads(limit=limit)
    return {"threads": threads}


@app.get("/threads/{thread_id}/messages")
async def get_thread_messages(thread_id: str, limit: Optional[int] = None):
    ensure_components_initialized()
    """Get messages from a thread."""
    if not thread_manager:
        raise HTTPException(status_code=503, detail="Thread manager not available")
    
    if not thread_manager.thread_exists(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    
    messages = thread_manager.get_thread_messages(thread_id, limit=limit)
    return {"thread_id": thread_id, "messages": messages}


@app.post("/threads/{thread_id}/messages", response_model=ChatResponse)
async def send_message(thread_id: str, request: SendMessageRequest):
    ensure_components_initialized()
    """Send a message to a thread and get an AI response."""
    if not all([retriever, generator, safety, thread_manager]):
        raise HTTPException(status_code=503, detail="Service components not fully initialized")
    
    if not thread_manager.thread_exists(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    
    # Store user message
    thread_manager.add_message(thread_id, "user", request.content)
    
    # Safety check
    should_answer, refusal_reason = safety.should_answer(request.content)
    
    if not should_answer:
        query_type, _ = safety.route_query(request.content)
        refusal = safety.generate_refusal(query_type, refusal_reason or "")
        
        # Store assistant refusal
        thread_manager.add_message(thread_id, "assistant", refusal)
        
        return ChatResponse(
            answer=refusal,
            citation_url=None,
            thread_id=thread_id,
            debug={"refused": True, "reason": refusal_reason} if DEBUG_MODE else None
        )
    
    # Get recent context for query expansion
    context = thread_manager.get_recent_context(thread_id)
    expanded_query = f"{context} {request.content}" if context else request.content
    
    # Retrieve relevant chunks
    retrieval_result = retriever.retrieve(expanded_query)
    
    if not retrieval_result['retrieved_chunks']:
        fallback_answer = generator.generate_fallback("https://www.indmoney.com/mutual-funds/amc/navi-mutual-fund")
        thread_manager.add_message(thread_id, "assistant", fallback_answer)
        
        return ChatResponse(
            answer=fallback_answer,
            citation_url="https://www.indmoney.com/mutual-funds/amc/navi-mutual-fund",
            thread_id=thread_id,
            debug={"no_context": True} if DEBUG_MODE else None
        )
    
    # Generate answer
    generation_result = generator.generate(
        request.content,
        retrieval_result['retrieved_chunks'],
        retrieval_result['primary_citation']
    )
    
    if generation_result['status'] == 'error':
        error_answer = "I'm sorry, but I encountered an error processing your request. Please try again."
        thread_manager.add_message(thread_id, "assistant", error_answer)
        
        return ChatResponse(
            answer=error_answer,
            citation_url=None,
            thread_id=thread_id,
            debug={"error": generation_result['error']} if DEBUG_MODE else None
        )
    
    # Store assistant response
    thread_manager.add_message(thread_id, "assistant", generation_result['answer'])
    
    return ChatResponse(
        answer=generation_result['answer'],
        citation_url=generation_result['citation_url'],
        thread_id=thread_id,
        debug={
            "validation": generation_result['validation'],
            "chunk_count": retrieval_result['chunk_count']
        } if DEBUG_MODE else None
    )


@app.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a thread."""
    ensure_components_initialized()
    if not thread_manager:
        raise HTTPException(status_code=503, detail="Thread manager not available")
    
    if not thread_manager.delete_thread(thread_id):
        raise HTTPException(status_code=404, detail="Thread not found")
    
    return {"message": "Thread deleted successfully"}


def main():
    """Run the FastAPI server."""
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
