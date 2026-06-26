#!/usr/bin/env python3
"""
Centralized configuration for TrustMed AI
Loads configuration from environment variables (with .env file support)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root if it exists
# This allows users to create a .env file instead of setting environment variables
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(env_path)
    # Silent load - no print statement to avoid cluttering output
else:
    # Try loading from current directory as fallback
    load_dotenv()

# ============================================
# Neo4j Configuration
# ============================================
NEO4J_URI = os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASS", "admin123")
NEO4J_DB = os.getenv("NEO4J_DB", "neo4j")

# ============================================
# HuggingFace Configuration
# ============================================
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
HF_API_KEY_ENV = "HUGGINGFACE_API_KEY"  # For backward compatibility

# ============================================
# Model Configuration
# ============================================
EMBED_MODEL_NAME = os.getenv(
    "EMBED_MODEL_NAME", 
    "sentence-transformers/all-MiniLM-L6-v2"
)
HF_MODEL_NAME = os.getenv(
    "HF_MODEL_NAME",
    "meta-llama/Llama-3.1-8B-Instruct"
)

# ============================================
# Path Configuration
# ============================================
# Paths relative to code/ directory, pointing to data/
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DISEASE_INDEX_PATH = os.path.join(DATA_DIR, "disease_index.faiss")
DISEASE_META_PATH = os.path.join(DATA_DIR, "disease_index_meta.json")
RAG_INDEX_PATH = os.path.join(DATA_DIR, "rag_chunks.faiss")
RAG_META_PATH = os.path.join(DATA_DIR, "rag_chunks_meta.json")

# ============================================
# Validation
# ============================================
def validate_config():
    """Validate that required configuration is present"""
    errors = []
    
    if not HUGGINGFACE_API_KEY:
        errors.append("HUGGINGFACE_API_KEY is not set. Please set it in .env file or as environment variable.")
    
    if errors:
        raise RuntimeError("\n".join(errors))
    
    return True

# Auto-validate on import (but allow override for testing)
if os.getenv("TRUSTMED_SKIP_VALIDATION") != "1":
    try:
        validate_config()
    except RuntimeError:
        # Don't fail on import - let individual modules handle it
        pass

