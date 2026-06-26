# TrustMed AI - Complete Setup and Run Guide

This comprehensive guide covers everything you need to set up and run the TrustMed AI application from scratch.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Step 1: Install Neo4j](#step-1-install-neo4j)
3. [Step 2: Set Up Python Environment](#step-2-set-up-python-environment)
4. [Step 3: Configure HuggingFace API Key](#step-3-configure-huggingface-api-key)
5. [Step 4: Load Data into Neo4j](#step-4-load-data-into-neo4j)
6. [Step 5: Build FAISS Indices](#step-5-build-faiss-indices)
7. [Step 6: Verify Setup](#step-6-verify-setup)
8. [Step 7: Run the Application](#step-7-run-the-application)
9. [Troubleshooting](#troubleshooting)
10. [Configuration Reference](#configuration-reference)

---

## Prerequisites

Before you begin, ensure you have:

- [ ] **Python 3.8+** installed (Python 3.12 recommended)
- [ ] **Neo4j Desktop** or Neo4j Server installed
- [ ] **HuggingFace account** with API key
- [ ] **Terminal/Command line** access
- [ ] **Git** (to clone the repository)

---

## Step 1: Install Neo4j

### Option A: Neo4j Desktop (Recommended for beginners)

1. **Download Neo4j Desktop:**
   - Go to https://neo4j.com/download/
   - Download Neo4j Desktop for your operating system
   - Install and launch Neo4j Desktop

2. **Create a new database:**
   - Click "New Project" or "Add Database"
   - Choose "Create a Local Database"
   - Set a name (e.g., "TrustMed")
   - Set password: `admin123` (or update it in `code/trustmed_agent.py` line 15 if you use a different password)
   - Click "Create"

3. **Start the database:**
   - Click the "Start" button next to your database
   - Wait for it to show "Active" status
   - Note: The default port is 7687 (bolt) and 7474 (HTTP)

### Option B: Neo4j Server (Advanced)

1. **Install Neo4j Server:**
   ```bash
   # On macOS with Homebrew
   brew install neo4j
   
   # Or download from https://neo4j.com/download/
   ```

2. **Start Neo4j:**
   ```bash
   neo4j start
   ```

3. **Set initial password:**
   - Open browser to http://localhost:7474
   - Default username: `neo4j`
   - Set password: `admin123` (or update in code)

---

## Step 2: Set Up Python Environment

### 2.1 Create Virtual Environment

```bash
cd /Users/jvb/Desktop/Trust_Med_AI
python3 -m venv venv
source venv/bin/activate
```

### 2.2 Install Dependencies

```bash
pip install -r code/requirements.txt
```

**Expected output:** All packages install successfully without errors.

---

## Step 3: Configure Application Settings

The application uses a `.env` file for configuration. This is the **recommended approach** as it keeps all settings in one place and makes setup easier.

### 3.1 Create the .env File

1. **Copy the example file:**
   ```bash
   cd /Users/jvb/Desktop/Trust_Med_AI
   cp .env.example .env
   ```

2. **Edit the `.env` file** with your favorite text editor:
   ```bash
   nano .env
   # or
   vim .env
   # or open in your IDE
   ```

### 3.2 Configure Neo4j Settings

In the `.env` file, update the Neo4j configuration if needed:

```bash
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASS=admin123
NEO4J_DB=neo4j
```

**Note:** If your Neo4j password is different from `admin123`, update `NEO4J_PASS` accordingly.

### 3.3 Configure HuggingFace API Key

1. **Get your HuggingFace API key:**
   - Go to https://huggingface.co/settings/tokens
   - Click "New token"
   - Give it a name (e.g., "TrustMed AI")
   - Select "Read" permissions
   - Click "Generate token"
   - **Copy the token immediately** (you won't see it again!)

2. **Add it to your `.env` file:**
   ```bash
   HUGGINGFACE_API_KEY=your-actual-token-here
   ```
   Replace `your-actual-token-here` with your actual token.

### 3.4 Verify Configuration

The application will automatically load the `.env` file when you run any script. You can verify it's working:

```bash
source venv/bin/activate
python code/verify_setup.py
```

This will check that your HuggingFace API key and Neo4j connection are configured correctly.

### 3.5 Alternative: Environment Variables (Optional)

If you prefer to use environment variables instead of a `.env` file, you can set them in your shell:

```bash
export HUGGINGFACE_API_KEY="your-token-here"
export NEO4J_URI="neo4j://127.0.0.1:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASS="admin123"
```

**Note:** The `.env` file approach is recommended as it's easier to manage and doesn't require setting variables in every terminal session.

---

## Step 4: Load Data into Neo4j

The application requires medical data to be loaded into Neo4j. Run these scripts in order:

### 4.1 Load Diseases

```bash
cd /Users/jvb/Desktop/Trust_Med_AI
source venv/bin/activate
python code/load_mayo_diseases_from_files.py
```

**Expected output:**
- Processes disease files from `data/diseases_parsed/`
- Creates Disease nodes in Neo4j
- Shows progress and completion message

### 4.2 Load Drugs

```bash
python code/load_mayo_drugs_to_neo4j.py
```

**Expected output:**
- Processes drug files from `data/drugs_parsed/`
- Creates Drug nodes in Neo4j
- Shows progress and completion message

### 4.3 Load Reddit Posts and KRTs

```bash
python code/load_krt_and_posts_to_neo4j.py
```

**Expected output:**
- Loads KRT definitions from `data/krt_definitions.json`
- Loads Reddit posts from `data/t2d_reddit_threads_tagged.jsonl`
- Creates Post and KRT nodes with relationships
- Shows progress and completion message

### 4.4 Verify Data Loaded

```bash
python code/verify_neo4j_data.py
```

**Expected output:**
- Shows count of Diseases, Drugs, Posts, and KRTs
- Verifies relationships are created

---

## Step 5: Build FAISS Indices

FAISS indices are required for fast similarity search. Build them after loading data:

### 5.1 Build Disease Index

```bash
python code/build_disease_index.py
```

**Expected output:**
- Downloads embedding model (first time only)
- Processes all diseases from Neo4j
- Creates `data/disease_index.faiss` and `data/disease_index_meta.json`
- Shows completion message with file paths

**Note:** This may take a few minutes on first run (model download).

### 5.2 Build RAG Corpus Index

```bash
python code/build_rag_corpus.py
```

**Expected output:**
- Processes diseases, drugs, and Reddit posts from Neo4j
- Creates text chunks and embeddings
- Creates `data/rag_chunks.faiss` and `data/rag_chunks_meta.json`
- Shows completion message with file paths

**Note:** This may take several minutes depending on data size.

---

## Step 6: Verify Setup

Run the comprehensive setup verification:

```bash
python code/verify_setup.py
```

**Should show:**
- ✅ Python version
- ✅ Dependencies installed
- ✅ HuggingFace API key set
- ✅ Neo4j connection successful
- ✅ FAISS index files exist

If any checks fail, address the issues before proceeding.

---

## Step 7: Run the Application

The application requires **TWO terminal windows** running simultaneously.

### 7.1 Start the Backend (Terminal 1)

1. **Open a terminal window**

2. **Navigate to the project:**
   ```bash
   cd /Users/jvb/Desktop/Trust_Med_AI
   ```

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Verify environment variables are set:**
   ```bash
   echo $HUGGINGFACE_API_KEY
   ```
   (Should show your token, not empty)

5. **Start the FastAPI backend:**
   ```bash
   ./code/start_backend.sh
   ```
   
   Or manually:
   ```bash
   cd code
   uvicorn fastapi_server:app --reload --port 8000
   ```

6. **Expected output:**
   ```
   INFO:     Uvicorn running on http://127.0.0.1:8000
   INFO:     Application startup complete.
   ```

7. **Test the backend:**
   - Open http://127.0.0.1:8000 in your browser
   - You should see: `{"TrustMed":"running","status":"ok"}`

8. **⚠️ Keep this terminal running!**

### 7.2 Start the UI (Terminal 2)

1. **Open a NEW terminal window** (keep Terminal 1 running!)

2. **Navigate to the project:**
   ```bash
   cd /Users/jvb/Desktop/Trust_Med_AI
   ```

3. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

4. **Start Streamlit:**
   ```bash
   ./code/start_ui.sh
   ```
   
   Or manually:
   ```bash
   cd code
   streamlit run trustmed_ui.py --server.headless true
   ```

5. **Expected:**
   - Browser automatically opens to http://localhost:8501
   - You see the TrustMed AI chat interface

### 7.3 Use the Application

1. **In the Streamlit UI**, you should see a chat interface
2. **Type a medical question**, for example:
   - "What are the symptoms and treatments for asthma?"
   - "How is type 2 diabetes treated?"
   - "What should I know about hypertension medications?"
   - "Tell me about GERD and how people cope with it"
3. **Press Enter** and wait for the AI to process your question
4. **The answer will appear** in the chat interface with:
   - Trusted Medical Information (from Mayo Clinic data)
   - Community Experiences (from Reddit posts/KRTs)
   - Safety / Next Steps (reminder to consult a clinician)
   - Sources / Citations (with clickable links)

---

## Troubleshooting

### Backend Issues

**Error: "HUGGINGFACE_API_KEY is not set"**
- Solution: Make sure you've created a `.env` file from `.env.example` and added your HuggingFace API key
- Verify: Run `python code/verify_setup.py` to check configuration
- Alternative: Set environment variable: `export HUGGINGFACE_API_KEY="your-key"`
- Restart the backend after setting

**Error: "Connection refused" or Neo4j errors**
- Solution: Make sure Neo4j is running
- Check: Run `python code/test_neo4j_connection.py`
- Verify: Neo4j Desktop shows database as "Active"
- Check password matches your `.env` file (`NEO4J_PASS` setting)

**Error: "ModuleNotFoundError"**
- Solution: Activate virtual environment: `source venv/bin/activate`
- Reinstall: `pip install -r code/requirements.txt`

**Error: "Missing FAISS index"**
- Solution: Run the build scripts:
  ```bash
  source venv/bin/activate
  python code/build_disease_index.py
  python code/build_rag_corpus.py
  ```

**Slow first response**
- Normal: First query loads models (may take 10-30 seconds)
- Subsequent queries should be faster
- Use `/warmup` endpoint to pre-load models: `curl http://127.0.0.1:8000/warmup`

### UI Issues

**Error: "Failed to contact backend"**
- Solution: Make sure Terminal 1 (backend) is still running
- Check: Visit http://127.0.0.1:8000 - should show `{"TrustMed":"running","status":"ok"}`
- Verify: Backend is on port 8000 (check Terminal 1 output)
- Check: Backend shows "Application startup complete"

**Browser doesn't open automatically**
- Solution: Manually navigate to http://localhost:8501
- Check: Terminal 2 shows Streamlit is running

**Python quit unexpectedly (macOS)**
- Solution: This is a known Streamlit issue on macOS
- The `start_ui.sh` script already includes `--server.headless true` to prevent this
- If it still happens, try: `streamlit run code/trustmed_ui.py --server.headless true --browser.gatherUsageStats false`

### Neo4j Issues

**Error: "Unable to connect"**
- Solution: Start Neo4j database in Neo4j Desktop
- Check password matches your `.env` file (`NEO4J_PASS` setting)
- Verify port 7687 is not blocked by firewall

**Error: "Authentication failed"**
- Solution: Password mismatch - update `NEO4J_PASS` in your `.env` file
- Or reset Neo4j password to match what's in your `.env` file

**No data in Neo4j**
- Solution: Run the data loading scripts (Step 4)
- Verify: Run `python code/verify_neo4j_data.py` to check counts

---

## Configuration Reference

### Environment Variables

| Variable | Description | How to Set |
|----------|-------------|------------|
| `HUGGINGFACE_API_KEY` | HuggingFace API token for LLM access | `export HUGGINGFACE_API_KEY="your-token"` |

### Code Configuration

| Setting | Location | How to Change |
|---------|----------|---------------|
| Neo4j URI | `.env` file | Edit `NEO4J_URI` |
| Neo4j Username | `.env` file | Edit `NEO4J_USER` |
| Neo4j Password | `.env` file | Edit `NEO4J_PASS` |
| Neo4j Database | `.env` file | Edit `NEO4J_DB` |
| HuggingFace API Key | `.env` file | Edit `HUGGINGFACE_API_KEY` |
| Backend URL | `code/trustmed_ui.py` | Edit line 8 |
| Backend Port | `code/fastapi_server.py` | Edit uvicorn command |
| UI Port | `code/start_ui.sh` | Edit streamlit command |

### Service Ports

| Component | Port | URL |
|-----------|------|-----|
| Neo4j Browser | 7474 | http://localhost:7474 |
| Neo4j Bolt | 7687 | neo4j://127.0.0.1:7687 |
| FastAPI Backend | 8000 | http://127.0.0.1:8000 |
| Streamlit UI | 8501 | http://localhost:8501 |

---

## Quick Reference Checklist

Before running, make sure:

- [ ] Neo4j is installed and running
- [ ] Neo4j database is active (shows "Active" in Neo4j Desktop)
- [ ] `.env` file created from `.env.example` and configured
- [ ] Neo4j password in `.env` matches your Neo4j database password
- [ ] HuggingFace API key added to `.env` file
- [ ] Data loaded into Neo4j (diseases, drugs, Reddit posts)
- [ ] FAISS indices built (`data/disease_index.faiss`, `data/rag_chunks.faiss`)
- [ ] Virtual environment is created: `python3 -m venv venv`
- [ ] Dependencies installed: `pip install -r code/requirements.txt`
- [ ] Backend running in Terminal 1 on port 8000
- [ ] UI running in Terminal 2 on port 8501

---

## Next Steps

After setup, you may want to:

- **Run evaluations:** See [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md)
- **Understand community experiences:** See [COMMUNITY_EXPERIENCES_FLOW.md](COMMUNITY_EXPERIENCES_FLOW.md)
- **Explore the codebase:** Check `code/` directory for implementation details

---

## Need Help?

If you encounter issues:

1. Check the error message in the terminal
2. Verify each step in this guide
3. Check the troubleshooting section above
4. Make sure both terminals show the virtual environment is activated
5. Verify all prerequisites are met

**Good luck! 🚀**

---

## Important Notes

⚠️ **This is NOT a diagnostic tool** and does **NOT** replace a clinician. Always discuss your situation with a licensed healthcare provider.

The system combines:
- ✅ Trusted disease & treatment information (Mayo-style knowledge graph)
- 💊 Drug & supplement monographs (side effects, warnings, interactions)
- 🧩 Key Recurring Themes (KRTs) from real patient/community discussions
- 🔗 Links to similar Reddit threads (for human stories)
- 🤖 Llama-based answer synthesis with clear sections

