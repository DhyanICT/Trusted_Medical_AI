import json
import os
import re
from glob import glob
from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB

# Path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DISEASES_DIR = os.path.join(DATA_DIR, "diseases_parsed")

JUNK_SUBSTRINGS = [
    "There is a problem with",
    "Sign up for free and stay up to date",
    "ErrorEmail field is required",
    "ErrorInclude a valid email address",
    "You'll soon start receiving the latest Mayo Clinic health information",
    "Please, try again in a couple of minutes"
]

def slugify(s: str) -> str:
    s = s.lower().replace("-", "_")
    s = re.sub(r"[^a-z0-9_]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"

def clean_lines(lines):
    cleaned = []
    for line in lines:
        text = line.strip()
        if not text:
            continue
        if any(bad in text for bad in JUNK_SUBSTRINGS):
            continue
        cleaned.append(text)
    return cleaned

def load_one_disease(session, d: dict, file_id: str):
    source = d.get("source", "Mayo Clinic")
    url = d.get("url")
    title = d.get("title", "Unknown disease")
    overview = d.get("overview", "")
    last_accessed = d.get("last_accessed")

    # 🔑 NEW: use filename-based id to ensure uniqueness per file
    disease_id = slugify(file_id)

    session.run(
        """
        MERGE (dis:Disease {id: $id})
        SET dis.name = $name,
            dis.source = $source,
            dis.url = $url,
            dis.overview = $overview,
            dis.last_accessed = $last_accessed
        """,
        id=disease_id,
        name=title,
        source=source,
        url=url,
        overview=overview,
        last_accessed=last_accessed,
    )

    sections = d.get("sections", {})

    def create_related(label, rel_type, section_key):
        raw_lines = sections.get(section_key, [])
        lines = clean_lines(raw_lines)
        for text in lines:
            session.run(
                f"""
                MERGE (n:{label} {{text: $text}})
                MERGE (dis:Disease {{id: $d_id}})
                MERGE (dis)-[:{rel_type} {{source:'mayo'}}]->(n)
                """,
                text=text,
                d_id=disease_id,
            )

    create_related("Symptom",        "HAS_SYMPTOM",         "Symptoms")
    create_related("Cause",          "HAS_CAUSE",           "Causes")
    create_related("RiskFactor",     "HAS_RISK_FACTOR",     "Risk Factors")
    create_related("Complication",   "HAS_COMPLICATION",    "Complications")
    create_related("Prevention",     "HAS_PREVENTION",      "Prevention")
    create_related("DiagnosisPoint", "HAS_DIAGNOSIS_POINT", "Diagnosis")
    create_related("TreatmentStep",  "HAS_TREATMENT_STEP",  "Treatment")

def main():
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASS),
        encrypted=False
    )

    pattern = os.path.join(DISEASES_DIR, "**", "*.json")
    disease_files = glob(pattern, recursive=True)
    print(f"[INFO] DISEASES_DIR = {DISEASES_DIR}")
    print(f"[INFO] Found {len(disease_files)} JSON files matching pattern {pattern}")

    with driver.session(database=NEO4J_DB) as session:
        # 🔥 Clear old graph once so you start clean
        session.run("MATCH (n) DETACH DELETE n")

        loaded = 0
        failed = 0

        for path in disease_files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    d = json.load(f)

                if "title" not in d or "sections" not in d:
                    print(f"[WARN] Skipping {path} (missing 'title' or 'sections')")
                    failed += 1
                    continue

                file_id = os.path.splitext(os.path.basename(path))[0]
                print(f"[LOAD] {file_id}")

                load_one_disease(session, d, file_id)
                loaded += 1

                if loaded % 100 == 0:
                    print(f"[PROGRESS] Loaded {loaded} diseases...")

            except Exception as e:
                print(f"[ERROR] Failed to load {path}: {e}")
                failed += 1

    driver.close()
    print(f"[DONE] Loaded {loaded} disease files into Neo4j. Failed: {failed}")

if __name__ == "__main__":
    main()
