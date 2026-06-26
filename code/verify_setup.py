#!/usr/bin/env python3
"""
Setup verification script for TrustMed AI
Run this to check if everything is configured correctly before starting the app.
"""

import os
import sys

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("❌ Python version too old. Need 3.8+")
        return False

def check_dependencies():
    """Check if required packages are installed"""
    required = [
        "fastapi",
        "streamlit",
        "neo4j",
        "faiss",
        "numpy",
        "sentence_transformers",
        "huggingface_hub",
    ]
    missing = []
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_"))
            print(f"✅ {pkg} installed")
        except ImportError:
            print(f"❌ {pkg} NOT installed")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    return True

def check_huggingface_key():
    """Check if HuggingFace API key is set"""
    try:
        from config import HUGGINGFACE_API_KEY
        key = HUGGINGFACE_API_KEY
        if key:
            # Show first and last 4 chars for verification
            masked = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else "***"
            print(f"✅ HuggingFace API key is set: {masked}")
            return True
        else:
            print("❌ HUGGINGFACE_API_KEY not set in .env file or environment")
            print("   Set it in .env file or with: export HUGGINGFACE_API_KEY='your-key-here'")
            return False
    except ImportError:
        print("❌ Could not import config module")
        return False

def check_neo4j_connection():
    """Check if Neo4j is accessible"""
    try:
        from neo4j import GraphDatabase
        from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB
        
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
        with driver.session(database=NEO4J_DB) as session:
            result = session.run("RETURN 1 AS n")
            result.single()
        driver.close()
        print("✅ Neo4j connection successful")
        return True
    except Exception as e:
        print(f"❌ Neo4j connection failed: {e}")
        print("   Make sure Neo4j is running and credentials are correct")
        print("   Check .env file or config.py for connection settings")
        return False

def check_faiss_files():
    """Check if required FAISS index files exist"""
    # Path to data directory
    DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
    required_files = [
        os.path.join(DATA_DIR, "disease_index.faiss"),
        os.path.join(DATA_DIR, "disease_index_meta.json"),
        os.path.join(DATA_DIR, "rag_chunks.faiss"),
        os.path.join(DATA_DIR, "rag_chunks_meta.json"),
    ]
    missing = []
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {os.path.basename(file)} exists")
        else:
            print(f"❌ {os.path.basename(file)} NOT found")
            missing.append(os.path.basename(file))
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        print("   You may need to run: python code/build_disease_index.py")
        print("   And: python code/build_rag_corpus.py")
        return False
    return True

def main():
    print("=" * 60)
    print("TrustMed AI - Setup Verification")
    print("=" * 60)
    print()
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("HuggingFace API Key", check_huggingface_key),
        ("Neo4j Connection", check_neo4j_connection),
        ("FAISS Index Files", check_faiss_files),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"\n[{name}]")
        print("-" * 40)
        result = check_func()
        results.append(result)
    
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_passed = all(results)
    if all_passed:
        print("✅ All checks passed! You're ready to run the application.")
        print("\nNext steps:")
        print("  1. Terminal 1: ./start_backend.sh")
        print("  2. Terminal 2: ./start_ui.sh")
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        print("\nSee SETUP_AND_RUN_GUIDE.md for detailed instructions.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())


