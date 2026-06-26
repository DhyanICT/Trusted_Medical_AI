import json
import os
from neo4j import GraphDatabase

# --- Neo4j config: same as your working test ----
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB

DB_NAME = NEO4J_DB
# ------------------------------------------------

# Paths to data directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
KRT_DEFS_PATH = os.path.join(DATA_DIR, "krt_definitions.json")
POSTS_PATH = os.path.join(DATA_DIR, "t2d_reddit_threads_tagged.jsonl")


def get_driver():
    return GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASS),
        encrypted=False
    )


def load_krt_definitions(session):
    with open(KRT_DEFS_PATH, "r", encoding="utf-8") as f:
        krt_defs = json.load(f)

    for krt in krt_defs:
        session.run(
            """
            MERGE (k:KRT {id: $id})
            SET k.label = $label,
                k.category = $category,
                k.description = $description
            """,
            id=krt["id"],
            label=krt["label"],
            category=krt["category"],
            description=krt["description"],
        )
    print(f"Loaded {len(krt_defs)} KRT nodes.")


def get_t2d_disease_id(session):
    # Try to find Type 2 diabetes disease node
    result = session.run(
        """
        MATCH (d:Disease)
        WHERE toLower(d.name) CONTAINS 'type 2 diabetes'
        RETURN d.id AS id, d.name AS name
        LIMIT 1
        """
    ).single()

    if not result:
        raise RuntimeError("Could not find a Disease node for 'Type 2 diabetes'.")

    print(f"Using Disease id for Type 2 diabetes: {result['id']} (name={result['name']})")
    return result["id"]


def load_posts_and_links(session, t2d_id: str):
    count = 0
    with open(POSTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)

            post_id = obj.get("post_id")
            thread_id = obj.get("thread_id")
            text = obj.get("text", "")
            source = obj.get("source", "")
            url = obj.get("thread_url", "")
            role = obj.get("role", "")

            krt_ids = obj.get("krt_ids", [])

            # Create / update Post node
            session.run(
                """
                MERGE (p:Post {post_id: $post_id})
                SET p.thread_id = $thread_id,
                    p.text = $text,
                    p.source = $source,
                    p.url = $url,
                    p.role = $role
                """,
                post_id=post_id,
                thread_id=thread_id,
                text=text,
                source=source,
                url=url,
                role=role,
            )

            # Link Post -> Disease (Type 2 diabetes)
            session.run(
                """
                MATCH (p:Post {post_id: $post_id})
                MATCH (d:Disease {id: $d_id})
                MERGE (p)-[:ABOUT]->(d)
                """,
                post_id=post_id,
                d_id=t2d_id,
            )

            # Link Post -> KRTs
            for krt_id in krt_ids:
                session.run(
                    """
                    MATCH (p:Post {post_id: $post_id})
                    MATCH (k:KRT {id: $krt_id})
                    MERGE (p)-[:HAS_THEME]->(k)
                    """,
                    post_id=post_id,
                    krt_id=krt_id,
                )

            count += 1
            if count % 100 == 0:
                print(f"Loaded {count} posts...")

    print(f"Finished loading {count} posts.")


def main():
    driver = get_driver()
    with driver.session(database=DB_NAME) as session:
        # 1) Load KRT nodes
        load_krt_definitions(session)

        # 2) Find Type 2 diabetes disease node
        t2d_id = get_t2d_disease_id(session)

        # 3) Load posts + relationships
        load_posts_and_links(session, t2d_id)

    driver.close()
    print("All done.")


if __name__ == "__main__":
    main()
