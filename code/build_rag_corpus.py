# build_rag_corpus.py
"""
Build the RAG corpus from Neo4j:

- Disease nodes (Mayo disease overviews)
- Drug nodes (Mayo drug overviews)
- Reddit Post nodes linked to diseases (with optional KRT labels)

Outputs:
  - rag_chunks.faiss
  - rag_chunks_meta.json
"""

import json
import os

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from neo4j import GraphDatabase

# === Neo4j config ===
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB, EMBED_MODEL_NAME

DB_NAME = NEO4J_DB

# === Outputs ===
# Output to data/ directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_INDEX = os.path.join(DATA_DIR, "rag_chunks.faiss")
OUT_META = os.path.join(DATA_DIR, "rag_chunks_meta.json")


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


def simple_chunks(text: str, max_chars: int = 800):
    """
    Very simple text chunker based on paragraphs and max length.
    """
    text = (text or "").strip()
    if not text:
        return []

    paras = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    cur = ""

    for p in paras:
        if len(cur) + len(p) + 1 > max_chars:
            if cur:
                chunks.append(cur.strip())
            cur = p
        else:
            cur = (cur + " " + p).strip()

    if cur:
        chunks.append(cur.strip())

    return chunks


def fetch_corpus():
    """
    Collect chunks from:
    - Disease nodes
    - Drug nodes
    - Reddit Post nodes (if present)
    """
    driver = get_driver()
    docs = []

    with driver.session(database=DB_NAME) as session:
        # 1) Diseases
        res = session.run("""
            MATCH (d:Disease)
            RETURN id(d) AS id, d.name AS name, d.overview AS overview, 
                   coalesce(d.url, '') AS url, coalesce(d.source, 'Mayo Clinic') AS source
        """)
        for r in res:
            did = r["id"]
            name = r["name"] or ""
            overview = r["overview"] or ""
            url = r["url"] or ""
            source = r["source"] or "Mayo Clinic"
            if not (name or overview):
                continue
            base_text = f"{name}. {overview}".strip()
            for ch in simple_chunks(base_text, max_chars=800):
                docs.append({
                    "kind": "disease",
                    "disease_id": did,
                    "title": name,
                    "section": "overview",
                    "url": url,
                    "source": source,
                    "text": ch,
                })

        # 2) Drugs
        res = session.run("""
            MATCH (dr:Drug)
            RETURN id(dr) AS id, dr.name AS name, dr.overview AS overview,
                   coalesce(dr.url, '') AS url, coalesce(dr.source, 'Mayo Clinic') AS source
        """)
        for r in res:
            rid = r["id"]
            name = r["name"] or ""
            overview = r["overview"] or ""
            url = r["url"] or ""
            source = r["source"] or "Mayo Clinic"
            if not (name or overview):
                continue
            base_text = f"{name}. {overview}".strip()
            for ch in simple_chunks(base_text, max_chars=800):
                docs.append({
                    "kind": "drug",
                    "drug_id": rid,
                    "title": name,
                    "section": "overview",
                    "url": url,
                    "source": source,
                    "text": ch,
                })

        # 3) Reddit Posts (if present)
        # We keep this robust with COALESCE and OPTIONAL KRTs.
        res = session.run("""
            MATCH (p:Post)-[:ABOUT]->(d:Disease)
            OPTIONAL MATCH (p)-[:HAS_KRT]->(k:KRT)
            RETURN 
                id(p) AS post_id,
                id(d) AS disease_id,
                d.name AS disease_name,
                coalesce(p.title, '') AS title,
                coalesce(p.body, p.text, '') AS body,
                collect(DISTINCT k.label) AS krt_labels,
                coalesce(p.url, '') AS url
        """)
        for r in res:
            pid = r["post_id"]
            did = r["disease_id"]
            disease_name = r["disease_name"] or ""
            title = r["title"] or ""
            body = r["body"] or ""
            labels = r["krt_labels"] or []
            url = r["url"] or ""
            if not body:
                continue

            prefix = f"Reddit: {title or '[no title]'}"
            label_str = ", ".join(labels) if labels else "None"
            base_text = f"{prefix}\nDisease: {disease_name}\nKRTs: {label_str}\n\n{body}"

            for ch in simple_chunks(base_text, max_chars=800):
                docs.append({
                    "kind": "reddit",
                    "post_id": pid,
                    "disease_id": did,
                    "title": title or disease_name,
                    "krt_labels": labels,
                    "url": url,
                    "source": "Reddit",
                    "text": ch,
                })

    driver.close()
    return docs


def main():
    print(f"[INFO] Using embedding model: {EMBED_MODEL_NAME}")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    docs = fetch_corpus()
    print(f"[INFO] Collected {len(docs)} text chunks from Neo4j.")

    if not docs:
        print("[ERROR] No RAG chunks found. Check Disease, Drug, and Post nodes.")
        return

    texts = [d["text"] for d in docs]

    print("[INFO] Encoding chunks...")
    embs = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=True,
        normalize_embeddings=True,
    )
    embs = np.asarray(embs, dtype="float32")

    if embs.ndim != 2 or embs.shape[0] == 0:
        print("[ERROR] Embedding model returned no vectors.")
        return

    dim = embs.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embs)

    faiss.write_index(index, OUT_INDEX)
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Saved {len(docs)} chunks to:")
    print(f"  {OUT_INDEX}")
    print(f"  {OUT_META}")


if __name__ == "__main__":
    main()
