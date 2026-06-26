# build_disease_index.py
"""
Build FAISS index over Disease nodes to detect the most relevant disease(s)
for a user question using embeddings.
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

# Output to data/ directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
OUT_INDEX = os.path.join(DATA_DIR, "disease_index.faiss")
OUT_META = os.path.join(DATA_DIR, "disease_index_meta.json")


def get_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))


def fetch_diseases():
    """
    Fetch Disease nodes with name + overview (which you already loaded from Mayo JSON).
    """
    driver = get_driver()
    diseases = []
    with driver.session(database=DB_NAME) as session:
        result = session.run("""
            MATCH (d:Disease)
            RETURN id(d) AS id, d.name AS name, d.overview AS overview
        """)
        for r in result:
            d_id = r["id"]
            name = r["name"] or ""
            overview = r["overview"] or ""
            text = f"{name}. {overview}".strip()
            if not text:
                continue
            diseases.append({"id": d_id, "name": name, "text": text})
    driver.close()
    return diseases


def main():
    print(f"[INFO] Using embedding model: {EMBED_MODEL_NAME}")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    diseases = fetch_diseases()
    print(f"[INFO] Found {len(diseases)} diseases.")

    if not diseases:
        print("[ERROR] No Disease nodes found with name/overview.")
        return

    texts = [d["text"] for d in diseases]
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
    index = faiss.IndexFlatIP(dim)  # inner product on normalized vectors = cosine
    index.add(embs)

    faiss.write_index(index, OUT_INDEX)
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(diseases, f, ensure_ascii=False, indent=2)

    print(f"[DONE] Saved disease index to:")
    print(f"  {OUT_INDEX}")
    print(f"  {OUT_META}")


if __name__ == "__main__":
    main()
