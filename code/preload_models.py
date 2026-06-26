#!/usr/bin/env python3
"""
Pre-load models to avoid first-request delays
Run this once before starting the backend
"""

import os
from sentence_transformers import SentenceTransformer

EMBED_MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

print("=" * 60)
print("Pre-loading TrustMed AI Models")
print("=" * 60)
print()
print(f"Downloading embedding model: {EMBED_MODEL_NAME}")
print("This may take a few minutes on first run...")
print()

try:
    model = SentenceTransformer(EMBED_MODEL_NAME)
    print("✅ Embedding model loaded successfully!")
    print()
    
    # Test it
    test_text = "diabetes"
    embedding = model.encode([test_text], normalize_embeddings=True)
    print(f"✅ Model test successful (embedding dimension: {embedding.shape[1]})")
    print()
    print("=" * 60)
    print("✅ All models ready! You can now start the backend.")
    print("=" * 60)
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print()
    print("Make sure you have internet connection for first-time download.")
    exit(1)

