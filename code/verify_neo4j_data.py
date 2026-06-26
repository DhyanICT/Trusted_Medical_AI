#!/usr/bin/env python3
"""
Quick verification script to check what data is in Neo4j
"""

from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB

DB_NAME = NEO4J_DB

def verify_data():
    driver = GraphDatabase.driver(
        NEO4J_URI,
        auth=(NEO4J_USER, NEO4J_PASS),
        encrypted=False
    )
    
    with driver.session(database=DB_NAME) as session:
        print("=" * 60)
        print("Neo4j Data Verification")
        print("=" * 60)
        print()
        
        # Count total nodes
        result = session.run("MATCH (n) RETURN count(n) AS total")
        total = result.single()["total"]
        print(f"📊 Total nodes in database: {total}")
        print()
        
        # Count by label
        result = session.run("""
            MATCH (n)
            RETURN labels(n)[0] AS label, count(n) AS count
            ORDER BY count DESC
        """)
        
        print("📋 Nodes by type:")
        print("-" * 40)
        for record in result:
            label = record["label"] or "No label"
            count = record["count"]
            print(f"  {label:20s} : {count:>6,}")
        print()
        
        # Sample Disease nodes
        result = session.run("""
            MATCH (d:Disease)
            RETURN d.id AS id, d.name AS name, d.source AS source
            LIMIT 5
        """)
        
        diseases = list(result)
        if diseases:
            print(f"🏥 Sample Disease nodes (showing {len(diseases)} of many):")
            print("-" * 40)
            for record in diseases:
                print(f"  ID: {record['id']}")
                print(f"  Name: {record['name']}")
                print(f"  Source: {record['source']}")
                print()
        else:
            print("⚠️  No Disease nodes found!")
            print()
        
        # Count relationships
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS total")
        rel_count = result.single()["total"]
        print(f"🔗 Total relationships: {rel_count:,}")
        print()
        
        # Relationship types
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS rel_type, count(r) AS count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print("🔗 Top relationship types:")
        print("-" * 40)
        for record in result:
            rel_type = record["rel_type"]
            count = record["count"]
            print(f"  {rel_type:25s} : {count:>8,}")
        print()
        
        # Check for related nodes (symptoms, causes, etc.)
        result = session.run("""
            MATCH (d:Disease)-[r]->(related)
            RETURN type(r) AS rel_type, labels(related)[0] AS related_label, count(*) AS count
            ORDER BY count DESC
            LIMIT 10
        """)
        
        print("🔗 Disease relationships:")
        print("-" * 40)
        for record in result:
            rel_type = record["rel_type"]
            related_label = record["related_label"]
            count = record["count"]
            print(f"  Disease -[{rel_type}]-> {related_label:20s} : {count:>6,}")
        print()
        
        # Check one disease with all its relationships
        result = session.run("""
            MATCH (d:Disease)
            OPTIONAL MATCH (d)-[r]->(related)
            WITH d, type(r) AS rel_type, labels(related)[0] AS related_label, count(related) AS count
            RETURN d.name AS name, collect({type: rel_type, label: related_label, count: count}) AS rels
            LIMIT 1
        """)
        
        sample = result.single()
        if sample and sample["name"]:
            print(f"📝 Example: '{sample['name']}' relationships:")
            print("-" * 40)
            for rel in sample["rels"]:
                if rel["type"]:
                    print(f"  -[{rel['type']}]-> {rel['label']}: {rel['count']} nodes")
            print()
        
    driver.close()
    print("=" * 60)
    print("✅ Verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    verify_data()

