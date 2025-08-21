
from convert_cypher_to_gql_deepseek import convert_cypher_to_gql as LLM

print(LLM("MATCH (f:Filing)-[:ORIGINATOR|:BENEFITS]->(e:Entity) WITH f, COUNT(DISTINCT e) AS entityCount ORDER BY entityCount DESC LIMIT 3 RETURN f.sar_id AS filing_id, entityCount"))

