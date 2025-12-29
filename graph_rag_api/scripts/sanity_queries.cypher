// Sanity check queries for debugging the Neo4j graph
// Run these in Neo4j Browser or cypher-shell

// 1. Check total entity count
MATCH (e:Entity)
RETURN count(e) AS total_entities;

// 2. Count entities by type
MATCH (e:Entity)
RETURN e.type AS entity_type, count(e) AS count
ORDER BY count DESC;

// 3. Check relationship types
MATCH ()-[r]->()
RETURN type(r) AS rel_type, count(r) AS count
ORDER BY count DESC;

// 4. Find sample components
MATCH (e:Entity {type: 'component'})
RETURN e.id AS component_id, e.layer AS layer
LIMIT 20;

// 5. Find sample incidents
MATCH (e:Entity {type: 'incident'})
RETURN e.id AS incident_id, e.severity AS severity, e.version AS version
LIMIT 10;

// 6. Check relationships from a specific incident
MATCH (incident:Entity {type: 'incident', id: '128638'})-[r]->(target:Entity)
RETURN type(r) AS rel_type, target.id AS target_id, target.type AS target_type
LIMIT 20;

// 7. Find anchors for a test question (example: "kubelet crash")
MATCH (e:Entity)
WHERE e.type IN ['component', 'root_cause', 'failure_mode', 'concept']
AND (
    toLower(e.id) CONTAINS 'kubelet'
    OR toLower(e.id) CONTAINS 'crash'
)
RETURN e.id AS id, e.type AS type
ORDER BY 
    CASE e.type
        WHEN 'component' THEN 3
        WHEN 'root_cause' THEN 2
        WHEN 'failure_mode' THEN 2
        WHEN 'concept' THEN 1
    END DESC
LIMIT 15;

// 8. Test APOC path expansion (requires APOC plugin)
// First check if APOC is available:
CALL dbms.components() YIELD name, versions, edition
WHERE name = 'APOC'
RETURN name, versions, edition;

// 9. Test path expansion from an anchor (example: kubelet)
MATCH (start:Entity {id: 'kubelet'})
CALL apoc.path.expandConfig(start, {
    relationshipFilter: 'AFFECTS<|CAUSED_BY<|EXHIBITS<|TRIGGERED_BY<|ACTIVATES<|LEADS_TO>|USES>|DEPENDS_ON>|INVOLVES<',
    minLevel: 1,
    maxLevel: 2,
    bfs: true,
    limit: 100,
    uniqueness: 'NODE_PATH'
})
YIELD path
RETURN path
LIMIT 10;

// 10. Count relationships in expanded subgraph
MATCH (start:Entity {id: 'kubelet'})
CALL apoc.path.expandConfig(start, {
    relationshipFilter: 'AFFECTS<|CAUSED_BY<|EXHIBITS<|TRIGGERED_BY<|ACTIVATES<|LEADS_TO>|USES>|DEPENDS_ON>|INVOLVES<',
    minLevel: 1,
    maxLevel: 2,
    bfs: true,
    limit: 300,
    uniqueness: 'NODE_PATH'
})
YIELD path
WITH relationships(path) AS rels
UNWIND rels AS rel
WITH DISTINCT rel
RETURN type(rel) AS rel_type, count(*) AS count
ORDER BY count DESC;

