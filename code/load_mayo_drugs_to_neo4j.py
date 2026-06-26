# load_mayo_drugs_to_neo4j.py

import json
import os
from glob import glob
from neo4j import GraphDatabase

# --- Adjust these paths/creds ---
# Path to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
DRUGS_DIR = os.path.join(DATA_DIR, "drugs_parsed")
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB

DB_NAME = NEO4J_DB
# --------------------------------


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASS),
        encrypted=False,
    )


def _join_if_list(value):
    if isinstance(value, list):
        return "\n".join(str(v) for v in value)
    if isinstance(value, str):
        return value
    return None


def load_drug_file(session, path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    url = data.get("url")
    title = data.get("title") or data.get("name")
    source = data.get("source", "Mayo Clinic — Drugs & Supplements")
    sections = data.get("sections", {})
    last_accessed = data.get("last_accessed")
    meta = data.get("meta", {})

    if not title:
        print(f"[SKIP] No title in {path}")
        return

    # Use filename without extension as ID
    fname = os.path.basename(path)
    drug_id = os.path.splitext(fname)[0]

    # Generic name: everything before the first "("
    generic_name = title.split("(")[0].strip()

    # Route from meta if present
    route = meta.get("route")

    # Brand name
    brand_name = _join_if_list(sections.get("Brand Name"))

    # Overview: prefer top-level, else fall back to Description
    overview = data.get("overview") or _join_if_list(sections.get("Description"))

    # Side effects: main section + "More common" / "Rare" if present
    side_effects_main = _join_if_list(sections.get("Side Effects"))
    more_common = _join_if_list(sections.get("More common"))
    rare = _join_if_list(sections.get("Rare"))

    side_effects_parts = []
    if side_effects_main:
        side_effects_parts.append("Main side effects:\n" + side_effects_main)
    if more_common:
        side_effects_parts.append("More common:\n" + more_common)
    if rare:
        side_effects_parts.append("Rare:\n" + rare)
    side_effects = "\n\n".join(side_effects_parts) if side_effects_parts else None

    # Interactions: Drug Interactions + Other Interactions
    drug_inter = _join_if_list(sections.get("Drug Interactions"))
    other_inter = _join_if_list(sections.get("Other Interactions"))
    inter_parts = []
    if drug_inter:
        inter_parts.append("Drug interactions:\n" + drug_inter)
    if other_inter:
        inter_parts.append("Other interactions (food, alcohol, tobacco):\n" + other_inter)
    interactions = "\n\n".join(inter_parts) if inter_parts else None

    # Warnings/Precautions: Precautions + Before Using + Other Medical Problems
    precautions = _join_if_list(sections.get("Precautions"))
    before_using = _join_if_list(sections.get("Before Using"))
    other_med_problems = _join_if_list(sections.get("Other Medical Problems"))
    warn_parts = []
    if precautions:
        warn_parts.append("Precautions:\n" + precautions)
    if before_using:
        warn_parts.append("Before using:\n" + before_using)
    if other_med_problems:
        warn_parts.append("Other medical problems:\n" + other_med_problems)
    warnings = "\n\n".join(warn_parts) if warn_parts else None

    # Usage: Proper Use + Dosing + Missed Dose + Storage
    proper_use = _join_if_list(sections.get("Proper Use"))
    dosing = _join_if_list(sections.get("Dosing"))
    missed_dose = _join_if_list(sections.get("Missed Dose"))
    storage = _join_if_list(sections.get("Storage"))
    usage_parts = []
    if proper_use:
        usage_parts.append("Proper use:\n" + proper_use)
    if dosing:
        usage_parts.append("Dosing:\n" + dosing)
    if missed_dose:
        usage_parts.append("Missed dose:\n" + missed_dose)
    if storage:
        usage_parts.append("Storage:\n" + storage)
    usage = "\n\n".join(usage_parts) if usage_parts else None

    session.run(
        """
        MERGE (dr:Drug {id: $id})
        SET dr.name          = $name,
            dr.generic_name  = $generic_name,
            dr.brand_name    = $brand_name,
            dr.route         = $route,
            dr.source        = $source,
            dr.url           = $url,
            dr.overview      = $overview,
            dr.side_effects  = $side_effects,
            dr.interactions  = $interactions,
            dr.warnings      = $warnings,
            dr.usage         = $usage,
            dr.last_accessed = $last_accessed
        """,
        id=drug_id,
        name=title,
        generic_name=generic_name,
        brand_name=brand_name,
        route=route,
        source=source,
        url=url,
        overview=overview,
        side_effects=side_effects,
        interactions=interactions,
        warnings=warnings,
        usage=usage,
        last_accessed=last_accessed,
    )

    print(f"[LOAD] {drug_id} → {title}")


def main():
    print(f"[INFO] DRUGS_DIR = {DRUGS_DIR}")
    pattern = os.path.join(DRUGS_DIR, "**", "*.json")
    files = glob(pattern, recursive=True)
    print(f"[INFO] Found {len(files)} JSON files matching {pattern}")

    driver = get_driver()
    loaded = 0

    with driver.session(database=DB_NAME) as session:
        for path in files:
            try:
                load_drug_file(session, path)
                loaded += 1
            except Exception as e:
                print(f"[ERROR] {path}: {e}")

    driver.close()
    print(f"[DONE] Loaded {loaded} drug JSON files into Neo4j.")


if __name__ == "__main__":
    main()
