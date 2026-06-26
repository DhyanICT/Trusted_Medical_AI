from fastapi import FastAPI
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="TrustMed AI", version="1.0")

# Lazy import to avoid loading everything at startup
_answer_question_func = None

def get_answer_question():
    """Lazy load the agent to avoid startup delays"""
    global _answer_question_func
    if _answer_question_func is None:
        logger.info("Loading TrustMed agent (this may take a moment on first request)...")
        from trustmed_agent import answer_question
        _answer_question_func = answer_question
        logger.info("Agent loaded successfully!")
    return _answer_question_func


class QueryRequest(BaseModel):
    question: str


@app.post("/ask")
def ask_question(payload: QueryRequest):
    try:
        logger.info(f"Received question: {payload.question[:50]}...")
        import sys
        import traceback
        
        # Log memory usage if possible
        try:
            import psutil
            process = psutil.Process()
            mem_info = process.memory_info()
            logger.info(f"Memory usage: {mem_info.rss / 1024 / 1024:.1f} MB")
        except ImportError:
            pass  # psutil not installed, skip
        
        answer_question_func = get_answer_question()
        logger.info("Calling answer_question...")
        output = answer_question_func(payload.question)
        logger.info("Question answered successfully")
        return {
            "answer": output,
            "success": True
        }
    except MemoryError as e:
        logger.error(f"Memory error: {e}")
        return {
            "success": False,
            "error": "Out of memory. The system may need more RAM or the indices are too large."
        }
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        logger.error(traceback.format_exc())
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/")
def home():
    return {
        "TrustMed": "running",
        "status": "ok"
    }


@app.get("/health")
def health_check():
    """Health check endpoint that doesn't load models"""
    return {
        "status": "healthy",
        "backend": "running"
    }


@app.get("/warmup")
def warmup():
    """Warmup endpoint to pre-load models (call this after starting backend)"""
    try:
        logger.info("Warming up models...")
        answer_question_func = get_answer_question()
        # Test with a simple question
        test_output = answer_question_func("test")
        logger.info("Models warmed up successfully!")
        return {
            "status": "warmed_up",
            "message": "Models are ready to use"
        }
    except Exception as e:
        logger.error(f"Warmup failed: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
