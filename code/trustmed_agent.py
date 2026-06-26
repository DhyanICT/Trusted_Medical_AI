# trustmed_agent.py
import os
import json
from typing import List, Dict, Any, Optional

import faiss
import numpy as np
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
from huggingface_hub import InferenceClient

# Import centralized configuration
from config import (
    NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB,
    HUGGINGFACE_API_KEY, HF_API_KEY_ENV,
    EMBED_MODEL_NAME, HF_MODEL_NAME,
    DATA_DIR, DISEASE_INDEX_PATH, DISEASE_META_PATH,
    RAG_INDEX_PATH, RAG_META_PATH
)

# For backward compatibility
DB_NAME = NEO4J_DB

# === Globals ===
_driver = None
_embed_model = None
_disease_index = None
_disease_meta = None
_rag_index = None
_rag_meta = None
_hf_client = None


# ---------------- Neo4j driver ----------------

def get_driver():
    global _driver
    if _driver is None:
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    return _driver


# ---------------- Embedding model + indices ----------------

def get_embed_model():
    """Get embedding model with error handling"""
    global _embed_model
    if _embed_model is None:
        try:
            print("[DEBUG] Loading embedding model (this may take a moment)...")
            _embed_model = SentenceTransformer(EMBED_MODEL_NAME)
            print("[DEBUG] Embedding model loaded")
        except Exception as e:
            print(f"[ERROR] Failed to load embedding model: {e}")
            raise
    return _embed_model


def embed_text(text: str) -> np.ndarray:
    model = get_embed_model()
    emb = model.encode([text], normalize_embeddings=True)
    return np.asarray(emb, dtype="float32")


def load_faiss_index(path: str):
    if not os.path.exists(path):
        raise RuntimeError(f"Missing FAISS index at {path}")
    return faiss.read_index(path)


def lazy_load_indexes():
    """Lazy load FAISS indices with error handling"""
    global _disease_index, _disease_meta, _rag_index, _rag_meta
    try:
        if _disease_index is None:
            print("[DEBUG] Loading disease index...")
            _disease_index = load_faiss_index(DISEASE_INDEX_PATH)
            with open(DISEASE_META_PATH, "r", encoding="utf-8") as f:
                _disease_meta = json.load(f)
            print(f"[DEBUG] Disease index loaded: {len(_disease_meta)} entries")
        if _rag_index is None:
            print("[DEBUG] Loading RAG index...")
            _rag_index = load_faiss_index(RAG_INDEX_PATH)
            with open(RAG_META_PATH, "r", encoding="utf-8") as f:
                _rag_meta = json.load(f)
            print(f"[DEBUG] RAG index loaded: {len(_rag_meta)} entries")
    except Exception as e:
        print(f"[ERROR] Failed to load FAISS indices: {e}")
        raise


# ---------------- HF LLM client ----------------

def get_hf_client():
    global _hf_client
    if _hf_client is None:
        token = HUGGINGFACE_API_KEY
        if not token:
            raise RuntimeError(f"{HF_API_KEY_ENV} is not set. Please set it in .env file or as environment variable.")
        # Model is also passed explicitly in chat_completion for clarity
        _hf_client = InferenceClient(token=token)
    return _hf_client


# ---------------- Detection + retrieval ----------------

def detect_disease_via_embeddings(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Use FAISS index over Disease nodes to get top-k candidate diseases.
    """
    lazy_load_indexes()
    q_emb = embed_text(question)
    D, I = _disease_index.search(q_emb, top_k)
    sims = D[0]
    idxs = I[0]

    candidates = []
    for sim, idx in zip(sims, idxs):
        meta = _disease_meta[idx]
        candidates.append({
            "id": meta["id"],
            "name": meta["name"],
            "score": float(sim),
        })
    return candidates


def retrieve_rag_chunks(
    question: str,
    candidate_disease_ids: Optional[List[int]] = None,
    top_k: int = 15,
) -> List[Dict[str, Any]]:
    """
    Vector retrieve RAG chunks (Disease + Drug + Reddit).
    Optionally filter by disease_id.
    """
    lazy_load_indexes()
    q_emb = embed_text(question)
    # over-sample a bit, then filter
    D, I = _rag_index.search(q_emb, top_k * 3)
    sims = D[0]
    idxs = I[0]

    results = []
    for sim, idx in zip(sims, idxs):
        meta = _rag_meta[idx]
        if candidate_disease_ids:
            did = meta.get("disease_id")
            # some chunks (e.g., drugs) might not have disease_id; keep them
            if did is not None and did not in candidate_disease_ids:
                continue

        meta_copy = dict(meta)
        meta_copy["score"] = float(sim)
        results.append(meta_copy)
        if len(results) >= top_k:
            break

    return results


# ---------------- Optional structured context from KG ----------------

def get_medical_context_for_disease(session, disease_id: int) -> Dict[str, Any]:
    """
    Lightweight structured context: disease node core fields.
    Extend this if you have more relationships (SYMPTOM, RISK_FACTOR, etc.).
    """
    res = session.run(
        """
        MATCH (d:Disease)
        WHERE id(d) = $id
        RETURN d.name AS name, d.overview AS overview,
               coalesce(d.url, '') AS url, coalesce(d.source, 'Mayo Clinic') AS source
        """,
        id=disease_id,
    )
    rec = res.single()
    if not rec:
        return {}
    return {
        "name": rec["name"],
        "overview": rec["overview"],
        "url": rec["url"],
        "source": rec["source"],
    }


def get_drug_context_for_disease(
    session,
    disease_id: int,
    max_drugs: int = 5,
) -> List[Dict[str, Any]]:
    """
    Structured list of drugs linked to a disease, if you modeled such edges.
    If your schema uses a different relationship, adjust the MATCH.
    """
    res = session.run(
        """
        MATCH (d:Disease)-[:TREATED_BY|:HAS_DRUG]->(dr:Drug)
        WHERE id(d) = $id
        RETURN dr.name AS name, dr.overview AS overview,
               coalesce(dr.url, '') AS url, coalesce(dr.source, 'Mayo Clinic') AS source
        LIMIT $limit
        """,
        id=disease_id,
        limit=max_drugs,
    )
    drugs = []
    for r in res:
        drugs.append({
            "name": r["name"],
            "overview": r["overview"],
            "url": r["url"],
            "source": r["source"],
        })
    return drugs


# ---------------- Citation formatting ----------------

def format_citations(citations: List[Dict[str, Any]]) -> str:
    """Format citations for display - separated into Trusted Sources and Community Sources"""
    if not citations:
        return "No sources available."
    
    # Separate citations into trusted and community sources
    trusted_sources = []
    community_sources = []
    
    for cit in citations:
        kind = cit.get("kind", "")
        cit_type = cit.get("type", "")
        
        # Determine if it's a community source (Reddit) or trusted source (Mayo Clinic)
        if kind == "reddit" or "Reddit" in cit_type or "Community" in cit_type:
            community_sources.append(cit)
        else:
            trusted_sources.append(cit)
    
    # Sort each group by citation number
    trusted_sources.sort(key=lambda x: x.get("number", 999))
    community_sources.sort(key=lambda x: x.get("number", 999))
    
    formatted_sections = []
    
    # Format Trusted Sources section
    if trusted_sources:
        formatted_sections.append("### Trusted Sources")
        formatted_sections.append("")
        for cit in trusted_sources:
            num = cit.get("number", 0)
            title = cit.get("title", "Unknown")
            url = cit.get("url")
            source = cit.get("source", "Mayo Clinic")
            
            # Format citation with markdown link if URL is available
            if url and url.strip():
                # Use the URL as both link text and destination for clickability
                citation_text = f"[{num}] {title} ({source}) - [View Source]({url})"
            else:
                citation_text = f"[{num}] {title} ({source})"
            
            formatted_sections.append(citation_text)
        formatted_sections.append("")
    
    # Format Community Sources section
    if community_sources:
        formatted_sections.append("### Community Sources")
        formatted_sections.append("")
        for cit in community_sources:
            num = cit.get("number", 0)
            title = cit.get("title", "Unknown")
            url = cit.get("url")
            source = cit.get("source", "Reddit")
            
            # Format citation with markdown link if URL is available
            if url and url.strip():
                # Use the URL as both link text and destination for clickability
                citation_text = f"[{num}] {title} ({source}) - [View Source]({url})"
            else:
                citation_text = f"[{num}] {title} ({source})"
            
            formatted_sections.append(citation_text)
        formatted_sections.append("")
    
    return "\n".join(formatted_sections)


# ---------------- LLM answer construction (RAG + KG) ----------------

def build_llm_answer_rag(
    question: str,
    disease_candidates: List[Dict[str, Any]],
    disease_info: Optional[Dict[str, Any]],
    med_ctx: Optional[Dict[str, Any]],
    drug_ctx: List[Dict[str, Any]],
    rag_chunks: List[Dict[str, Any]],
) -> tuple[str, List[Dict[str, Any]]]:
    """
    Construct prompt and call LLM to synthesize a grounded answer.
    Collects citations from ALL sources: RAG chunks, disease context, and drug context.
    """

    disease_block = ""
    if disease_candidates:
        disease_block = "Candidate diseases (from search):\n"
        for c in disease_candidates:
            disease_block += f"- {c['name']} (score {c['score']:.2f})\n"

    # Build evidence block with clear source types and collect citations
    rag_block = ""
    reddit_present = False
    citations = []  # Collect citations for the response
    seen_sources = set()  # Track unique sources by (title, url) to avoid duplicates
    
    def add_citation(citation_dict: Dict[str, Any]) -> int:
        """Add a citation if not already seen, return citation number"""
        title = citation_dict.get("title", "")
        url = citation_dict.get("url", "")
        source_key = (title, url) if url else (title, None)
        
        if source_key in seen_sources:
            # Find existing citation number
            for cit in citations:
                if (cit.get("title") == title and cit.get("url") == url):
                    return cit["number"]
        
        # New citation
        citation_num = len(citations) + 1
        citation_dict["number"] = citation_num
        citations.append(citation_dict)
        seen_sources.add(source_key)
        return citation_num
    
    # Process RAG chunks and assign citation numbers sequentially
    for ch in rag_chunks[:12]:
        kind = ch.get("kind", "unknown")
        title = ch.get("title", "")
        score = ch.get("score", 0.0)
        url = ch.get("url", "")
        source = ch.get("source", "")
        
        if kind == "disease":
            src_type = "Trusted Disease Article (Mayo)"
        elif kind == "drug":
            src_type = "Trusted Drug Monograph (Mayo)"
        elif kind == "reddit":
            src_type = "Community Reddit Post"
            reddit_present = True
        else:
            src_type = "Other"

        # Add citation and get its number
        citation_num = add_citation({
            "type": src_type,
            "title": title,
            "url": url if url else None,
            "source": source if source else ("Reddit" if kind == "reddit" else None),
            "kind": kind,
        })
        citation_label = f"[{citation_num}]"

        # Build passage header with citation number
        header = f"{citation_label} {src_type} – {title} (score {score:.2f})"
        rag_block += header + "\n"
        if url:
            rag_block += f"URL: {url}\n"
        rag_block += ch["text"][:1200] + "\n\n"
    
    # Also add citations from structured context (disease and drugs from Neo4j)
    # These might not be in RAG chunks but are used in the answer
    if med_ctx and med_ctx.get("name"):
        add_citation({
            "type": "Trusted Disease Article (Mayo)",
            "title": med_ctx.get("name", ""),
            "url": med_ctx.get("url") if med_ctx.get("url") else None,
            "source": med_ctx.get("source", "Mayo Clinic"),
            "kind": "disease",
        })
    
    for drug in drug_ctx:
        if drug.get("name"):
            add_citation({
                "type": "Trusted Drug Monograph (Mayo)",
                "title": drug.get("name", ""),
                "url": drug.get("url") if drug.get("url") else None,
                "source": drug.get("source", "Mayo Clinic"),
                "kind": "drug",
            })

    client = get_hf_client()

    system_prompt = """
You are a cautious, evidence-grounded medical information assistant.

You MUST:
- Base your answer ONLY on the provided evidence passages and structured context.
- Prefer trusted medical texts (Mayo disease/drug content) for factual info.
- Use community (Reddit) content ONLY as anecdotal examples, clearly labeled as such.
- Never guess diagnoses, never prescribe specific doses, and never adjust medications.
- Always include a Safety / Next Steps section reminding the user to talk to their clinician.

If the question is generic (e.g., "I have hypertension"), treat it as general ADULT disease unless the question clearly indicates a child, pregnancy, or a specific subtype (like pulmonary hypertension).
"""

    user_prompt = f"""
User question:
{question}

{disease_block}

Structured medical context (may be empty):
{json.dumps(med_ctx or {}, indent=2)}

Structured drug context (may be empty):
{json.dumps(drug_ctx or [], indent=2)}

Evidence passages (trusted + community):
{rag_block}

Write a clear, patient-friendly answer with this structure:

1. Trusted Medical Information
   - Brief definition and why it matters.
   - Main symptoms / clinical picture (only if relevant to the question).
   - Treatment overview focusing on MEDICATION CLASSES and how they work, using the drug info when available.
   - How diet & lifestyle fit in (especially if the user asks about food, exercise, or weight).
   - **IMPORTANT: When referencing information from sources, cite them using [1], [2], etc. matching the passage numbers above.**

2. Community Experiences
   - ONLY if Reddit/community passages are present (you will see passages labeled "Community Reddit Post").
   - Summarize common themes and concerns from those posts.
   - Make it explicit that these are anecdotal experiences, not medical advice.
   - **CRITICAL: When mentioning Reddit experiences, you MUST cite them using the citation numbers from the passages above (e.g., [1], [2], etc.). Each Reddit post passage has a number - use that exact number.**

3. Safety / Next Steps
   - Emphasize that this is not personal medical advice or a diagnosis.
   - Encourage the user to discuss medications, doses, and major changes with their clinician.
   - Suggest when to seek urgent in-person care (e.g., severe or rapidly worsening symptoms).

**NOTE: Do NOT include a "Sources / Citations" section in your answer. The citations will be automatically appended after your response.**

Do NOT mention internal implementation details (KRTs, FAISS, Neo4j, etc.) in the answer.
"""

    # ---- FIX: use chat_completion instead of text_generation ----
    resp = client.chat_completion(
        model=HF_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        max_tokens=900,
        temperature=0.25,
    )

    # huggingface_hub chat_completion usually returns:
    # resp.choices[0].message["content"]
    try:
        answer = resp.choices[0].message["content"]
    except Exception:
        # Fallback, in case the structure is slightly different
        answer = str(resp)
    
    # Format citations for display - use our authoritative list from retrieved chunks
    formatted_citations = format_citations(citations)
    
    # Remove any existing citations section from LLM response and replace with our authoritative list
    # This ensures all retrieved sources (including Reddit) are properly cited
    import re
    # Remove existing citations sections
    answer = re.sub(r'\n## Sources / Citations.*$', '', answer, flags=re.DOTALL)
    answer = re.sub(r'\n### Sources / Citations.*$', '', answer, flags=re.DOTALL)
    answer = re.sub(r'\nCitations:.*$', '', answer, flags=re.DOTALL)
    answer = re.sub(r'\nSources:.*$', '', answer, flags=re.DOTALL)
    
    # Append our authoritative citations list
    if citations:
        answer += "\n\n## Sources / Citations\n\n" + formatted_citations

    return answer, citations


# ---------------- Public entrypoint ----------------

def answer_question(question: str) -> str:
    """
    Hybrid KG + RAG pipeline:
    - Detect diseases via embeddings.
    - Retrieve relevant text chunks (diseases, drugs, Reddit).
    - Optionally use Neo4j for extra structured context.
    - Ask LLM to synthesize a grounded answer with citations.
    
    Returns: Answer string with citations included.
    """
    # 1) Candidate diseases
    disease_candidates = detect_disease_via_embeddings(question, top_k=5)
    good_candidates = [c for c in disease_candidates if c["score"] > 0.3]
    disease_info = good_candidates[0] if good_candidates else None
    candidate_ids = [c["id"] for c in good_candidates if c["id"] is not None]

    # 2) RAG retrieval
    rag_chunks = retrieve_rag_chunks(
        question,
        candidate_disease_ids=candidate_ids,
        top_k=15,
    )

    # 3) Optional structured context from KG
    driver = get_driver()
    with driver.session(database=DB_NAME) as session:
        med_ctx = None
        drug_ctx = []
        if disease_info and disease_info["id"] is not None:
            d_id = disease_info["id"]
            med_ctx = get_medical_context_for_disease(session, d_id)
            drug_ctx = get_drug_context_for_disease(session, d_id, max_drugs=5)

    # 4) LLM synthesis
    final_answer, citations = build_llm_answer_rag(
        question=question,
        disease_candidates=good_candidates,
        disease_info=disease_info,
        med_ctx=med_ctx,
        drug_ctx=drug_ctx,
        rag_chunks=rag_chunks,
    )
    return final_answer


if __name__ == "__main__":
    q = "I have hypertension, can you help me with medications and diet?"
    print(answer_question(q))
