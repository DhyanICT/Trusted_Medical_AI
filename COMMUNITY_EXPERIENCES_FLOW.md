# How Community Experiences (Reddit Posts) Are Retrieved

## Overview
Community experiences come from Reddit posts that are stored in Neo4j and indexed in a FAISS vector database. They are retrieved using **semantic similarity search** based on the user's query.

## Step-by-Step Flow

### 1. Data Loading (Initial Setup)
**File**: `code/load_krt_and_posts_to_neo4j.py`

- Reddit posts are loaded from JSON files into Neo4j
- Each post is linked to a Disease node via `[:ABOUT]` relationship
- Posts are also linked to KRT (Key Recurring Themes) nodes via `[:HAS_THEME]` relationship
- **Current Limitation**: Only Type 2 diabetes posts are loaded (see `get_t2d_disease_id()`)

**Neo4j Structure**:
```
(Post)-[:ABOUT]->(Disease)
(Post)-[:HAS_THEME]->(KRT)
```

### 2. RAG Corpus Building
**File**: `code/build_rag_corpus.py`

When building the RAG corpus:
1. All Reddit posts are retrieved from Neo4j:
   ```cypher
   MATCH (p:Post)-[:ABOUT]->(d:Disease)
   OPTIONAL MATCH (p)-[:HAS_KRT]->(k:KRT)
   RETURN post_id, disease_id, title, body, url, krt_labels
   ```

2. Each post is formatted as:
   ```
   Reddit: [post title]
   Disease: [disease name]
   KRTs: [theme labels]
   
   [post body text]
   ```

3. Posts are chunked (split into ~800 character pieces) and embedded using sentence transformers
4. Embeddings are stored in FAISS index along with metadata (title, URL, disease_id, etc.)

### 3. Query Processing
**File**: `code/trustmed_agent.py` → `answer_question()`

When a user asks: *"What medications are used for type 2 diabetes?"*

#### Step 3a: Disease Detection
- Uses FAISS to find candidate diseases via semantic similarity
- Example: Finds "Type 2 diabetes" as a candidate with score > 0.3
- Gets `candidate_ids = [disease_id_for_t2d]`

#### Step 3b: RAG Retrieval
**Function**: `retrieve_rag_chunks()`

1. **Vector Search**: 
   - Embeds the user's question: "What medications are used for type 2 diabetes?"
   - Searches FAISS index for top 45 chunks (top_k * 3 = 15 * 3)
   - Returns chunks ranked by semantic similarity score

2. **Disease Filtering** (if candidate diseases found):
   ```python
   if candidate_disease_ids:
       did = meta.get("disease_id")
       if did is not None and did not in candidate_disease_ids:
           continue  # Skip chunks not related to candidate diseases
   ```
   - **Important**: Reddit posts have `disease_id`, so they ARE filtered by disease
   - Only posts linked to Type 2 diabetes will be included if Type 2 diabetes is detected

3. **Result**: Returns top 15 chunks (diseases, drugs, AND Reddit posts) sorted by relevance

### 4. Response Generation
**Function**: `build_llm_answer_rag()`

1. **RAG Chunks Passed to LLM**:
   - All retrieved chunks (including Reddit posts) are formatted with citation numbers:
   ```
   [1] Trusted Disease Article (Mayo) – Type 2 diabetes (score 0.85)
   URL: https://www.mayoclinic.org/...
   [Text content...]
   
   [2] Community Reddit Post – Managing T2D Medications (score 0.78)
   URL: https://www.reddit.com/...
   [Post content about medication experiences...]
   
   [3] Trusted Drug Monograph (Mayo) – Metformin (score 0.72)
   ...
   ```

2. **LLM Instructions**:
   - The LLM is explicitly told to include a "Community Experiences" section
   - It must cite Reddit posts using their citation numbers
   - It should summarize common themes from the Reddit posts

3. **Output**: The LLM generates a response with:
   - Trusted Medical Information (from Mayo sources)
   - **Community Experiences** (summarized from Reddit posts)
   - Safety / Next Steps

## Key Points

### ✅ How Reddit Posts Are Selected:
1. **Semantic Similarity**: Posts are retrieved based on how similar their content is to the user's query (vector search)
2. **Disease Filtering**: If a disease is detected, only posts linked to that disease are included
3. **Relevance Ranking**: Posts are ranked by similarity score, so most relevant posts appear first

### ⚠️ Current Limitations:
1. **Disease Coverage**: Only Type 2 diabetes posts are currently loaded
   - If you ask about "hypertension medications", no Reddit posts will be found
   - Solution: Load Reddit posts for other diseases

2. **Disease Matching**: Posts are filtered by `disease_id` from Neo4j
   - If disease detection fails or finds wrong disease, relevant posts might be excluded
   - The filtering is optional - if no candidate diseases are found, all posts are considered

### 🔧 How to Add More Community Experiences:

1. **For Other Diseases**:
   - Modify `load_krt_and_posts_to_neo4j.py` to load posts for other diseases
   - Link posts to their respective Disease nodes in Neo4j
   - Rebuild RAG corpus: `python code/build_rag_corpus.py`

2. **For Better Retrieval**:
   - The current system uses semantic similarity, which is good
   - Consider adding keyword matching for medication names
   - Could filter by KRT labels if user mentions specific themes

## Example Flow: "Type 2 Diabetes Medications"

1. **Query**: "What medications are used for type 2 diabetes?"
2. **Disease Detection**: Finds "Type 2 diabetes" (disease_id = "type-2-diabetes")
3. **RAG Retrieval**: 
   - Searches FAISS for similar content
   - Filters to only include chunks with `disease_id = "type-2-diabetes"` OR no disease_id
   - Returns: Disease articles, Drug monographs, AND Reddit posts about T2D medications
4. **LLM Processing**: 
   - Sees Reddit posts like "I've been on metformin for 2 years..." 
   - Summarizes common themes: medication effectiveness, side effects, lifestyle changes
5. **Response**: Includes "Community Experiences" section with cited Reddit posts

## Files Involved

- `code/load_krt_and_posts_to_neo4j.py` - Loads Reddit posts into Neo4j
- `code/build_rag_corpus.py` - Builds FAISS index with Reddit posts
- `code/trustmed_agent.py` - Retrieves and uses Reddit posts in responses
  - `retrieve_rag_chunks()` - Vector search for relevant chunks
  - `build_llm_answer_rag()` - Formats posts for LLM and generates response

