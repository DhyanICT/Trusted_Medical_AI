from neo4j import GraphDatabase

from config import NEO4J_URI, NEO4J_USER, NEO4J_PASS, NEO4J_DB

driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USER, NEO4J_PASS),
    encrypted=False
)

with driver.session(database=NEO4J_DB) as session:
    result = session.run("RETURN 1 AS n")
    print("Result:", result.single()["n"])

driver.close()
