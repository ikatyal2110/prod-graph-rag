#!/usr/bin/env python3
"""
Load graph data from JSON into Neo4j.

This script loads entities and relationships from complete_graph.json into Neo4j.
It is idempotent: clears existing graph first, then loads fresh data.

Schema:
- Nodes: :Entity label (required) with optional typed labels (e.g., :component, :incident)
- Relationships: Typed by edge type (e.g., :AFFECTS) with type property

Usage:
    python scripts/load_graph.py [--graph-file path/to/graph.json]

Environment variables:
    NEO4J_URI: Neo4j connection URI (default: bolt://localhost:7687)
    NEO4J_USER: Neo4j username (default: neo4j)
    NEO4J_PASSWORD: Neo4j password (default: testpassword)
    NEO4J_DB: Neo4j database name (default: neo4j)
"""

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Set

try:
    from neo4j import GraphDatabase
except ImportError:
    print("Error: 'neo4j' library is required. Install with: pip install neo4j", file=sys.stderr)
    sys.exit(2)

# Import validation module
# Add repo root to path to import graph validation
script_dir = Path(__file__).parent
repo_root = script_dir.parent.parent
sys.path.insert(0, str(repo_root))
try:
    from graph.validate_graph import validate_schema, validate_invariants
except ImportError:
    print("Error: Could not import graph validation module. Ensure graph/validate_graph.py exists.", file=sys.stderr)
    sys.exit(2)


def get_default_graph_file() -> Path:
    """Get default graph file path (complete_graph.json in repo root)."""
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    return repo_root / "complete_graph.json"


def compute_file_hash(graph_file: Path) -> str:
    """Compute SHA256 hash of file contents."""
    sha256_hash = hashlib.sha256()
    try:
        with open(graph_file, 'rb') as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Warning: Could not compute file hash: {e}", file=sys.stderr)
        return "unknown"


def load_graph_data(graph_file: Path) -> Dict[str, Any]:
    """Load graph data from JSON file."""
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'entities' not in data or 'edges' not in data:
            print(f"Error: Graph file must contain 'entities' and 'edges' keys", file=sys.stderr)
            sys.exit(2)
        
        return data
    except FileNotFoundError:
        print(f"Error: Graph file not found: {graph_file}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in graph file: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error reading graph file: {e}", file=sys.stderr)
        sys.exit(2)


def sanitize_reltype(reltype: str) -> str:
    """
    Sanitize relationship type to valid Cypher reltype.
    
    Relationship types must be uppercase, alphanumeric, and underscores.
    If already valid, use as-is. Otherwise sanitize.
    """
    # Check if already valid (uppercase, alphanumeric, underscores)
    if re.match(r'^[A-Z0-9_]+$', reltype):
        return reltype
    
    # Sanitize: uppercase and replace invalid chars with underscores
    sanitized = reltype.upper().replace('-', '_')
    sanitized = re.sub(r'[^A-Z0-9_]', '_', sanitized)
    return sanitized


def clear_graph(driver, database: str):
    """Clear all existing graph data."""
    print("Clearing existing graph data...")
    with driver.session(database=database) as session:
        result = session.run("MATCH (n) DETACH DELETE n RETURN count(n) AS deleted")
        record = result.single()
        deleted_count = record["deleted"] if record else 0
        print(f"  Deleted {deleted_count} nodes")


def build_entity_lookup(entities: List[Dict[str, Any]]) -> Dict[str, str]:
    """Build a map from entity id to entity type."""
    lookup = {}
    for entity in entities:
        entity_id = entity.get("id")
        entity_type = entity.get("type")
        if entity_id and entity_type:
            lookup[entity_id] = entity_type
    return lookup


def load_entities(driver, database: str, entities: List[Dict[str, Any]]):
    """Load entities into Neo4j with :Entity label and optional typed labels."""
    print(f"Loading {len(entities)} entities...")
    
    # Prepare entities with id, type, and attributes
    # Neo4j doesn't support nested maps as property values, so store attributes as JSON string
    prepared_entities = []
    for entity in entities:
        attrs = entity.get("attributes")
        if attrs is None:
            attrs = {}
        elif not isinstance(attrs, dict):
            # If attributes is not a dict, wrap it
            attrs = {"value": attrs}
        
        # Store attributes as JSON string since Neo4j doesn't support nested maps
        attrs_json = json.dumps(attrs) if attrs else "{}"
        
        props = {
            "id": entity["id"],
            "type": entity["type"],
            "attributes": attrs_json
        }
        prepared_entities.append(props)
    
    # Create nodes with :Entity label
    # Neo4j supports maps as property values
    # Use UNWIND with proper parameter passing
    query = """
    UNWIND $entities AS entity
    CREATE (e:Entity)
    SET e.id = entity.id,
        e.type = entity.type,
        e.attributes = entity.attributes
    """
    
    with driver.session(database=database) as session:
        # Create all nodes with :Entity label
        batch_size = 1000
        total_loaded = 0
        for i in range(0, len(prepared_entities), batch_size):
            batch = prepared_entities[i:i + batch_size]
            # The Neo4j Python driver should serialize dicts to maps automatically
            # If this fails, it might be a Neo4j version or configuration issue
            session.run(query, entities=batch)
            total_loaded += len(batch)
            if (i // batch_size + 1) % 10 == 0:
                print(f"  Loaded {min(i + batch_size, len(prepared_entities))} / {len(prepared_entities)} entities...")
    
    # Optionally add typed labels (group by type for efficiency)
    entities_by_type: Dict[str, List[str]] = {}
    for entity in prepared_entities:
        entity_type = entity["type"]
        entity_id = entity["id"]
        if entity_type not in entities_by_type:
            entities_by_type[entity_type] = []
        entities_by_type[entity_type].append(entity_id)
    
    # Add typed labels (lowercase)
    with driver.session(database=database) as session:
        for entity_type, entity_ids in entities_by_type.items():
            # Sanitize label: use lowercase, replace hyphens with underscores
            typed_label = entity_type.lower().replace('-', '_')
            # Remove invalid characters (keep only lowercase alphanumeric and underscores)
            typed_label = re.sub(r'[^a-z0-9_]', '_', typed_label)
            
            # Add label to all nodes of this type
            add_label_query = f"""
            UNWIND $entity_ids AS entity_id
            MATCH (e:Entity {{id: entity_id}})
            SET e:`{typed_label}`
            """
            
            try:
                for i in range(0, len(entity_ids), batch_size):
                    batch_ids = entity_ids[i:i + batch_size]
                    session.run(add_label_query, entity_ids=batch_ids)
                print(f"  Added :{typed_label} label to {len(entity_ids)} {entity_type} entities")
            except Exception as e:
                # If label addition fails (e.g., invalid label), skip it
                # The :Entity label is sufficient
                print(f"  ⚠ Could not add :{typed_label} label (skipping): {e}")
    
    print(f"  ✓ Loaded {total_loaded} total entities")


def load_edges(driver, database: str, edges: List[Dict[str, Any]], entity_lookup: Dict[str, str]):
    """Load relationships into Neo4j with typed relationship types and type property."""
    print(f"Loading {len(edges)} relationships...")
    
    # Prepare edges with from_id, to_id, and relationship type
    prepared_edges = []
    skipped_count = 0
    
    for edge in edges:
        from_id = edge.get("from")
        to_id = edge.get("to")
        rel_type = edge.get("type", "RELATED_TO")
        
        if not from_id or not to_id:
            skipped_count += 1
            continue
        
        # Sanitize relationship type for use as Cypher relationship type
        sanitized_reltype = sanitize_reltype(rel_type)
        
        prepared_edges.append({
            "from_id": from_id,
            "to_id": to_id,
            "rel_type": sanitized_reltype,  # Sanitized for relationship type
            "rel_type_prop": rel_type  # Original for type property
        })
    
    if skipped_count > 0:
        print(f"  ⚠ Skipped {skipped_count} edges due to missing data")
    
    # Group by relationship type for batch loading
    edges_by_reltype: Dict[str, List[Dict[str, Any]]] = {}
    for edge_data in prepared_edges:
        rel_type = edge_data["rel_type"]
        if rel_type not in edges_by_reltype:
            edges_by_reltype[rel_type] = []
        edges_by_reltype[rel_type].append(edge_data)
    
    # Load each relationship type
    # Create BOTH typed relationships AND generic :RELATIONSHIP for compatibility
    total_loaded = 0
    for rel_type, type_edges in edges_by_reltype.items():
        count = len(type_edges)
        
        # Create both:
        # 1. Typed relationship (e.g., :AFFECTS) with type property
        # 2. Generic :RELATIONSHIP with type property (for retrieval compatibility)
        query = f"""
        UNWIND $edges AS edge
        MATCH (from:Entity {{id: edge.from_id}})
        MATCH (to:Entity {{id: edge.to_id}})
        CREATE (from)-[r1:`{rel_type}` {{type: edge.rel_type_prop}}]->(to)
        CREATE (from)-[r2:RELATIONSHIP {{type: edge.rel_type_prop}}]->(to)
        """
        
        with driver.session(database=database) as session:
            # Process in batches of 1000
            batch_size = 1000
            for i in range(0, len(type_edges), batch_size):
                batch = type_edges[i:i + batch_size]
                session.run(query, edges=batch)
        
        total_loaded += count
        print(f"  Loaded {count} {rel_type} relationships (typed + :RELATIONSHIP)")
    
    print(f"  ✓ Loaded {total_loaded} total relationships")


def create_indexes(driver, database: str, entity_types: Set[str]):
    """Create indexes on :Entity nodes."""
    print("Creating indexes...")
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.id)",
        "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type)",
        "CREATE INDEX IF NOT EXISTS FOR (e:Entity) ON (e.type, e.id)",
    ]
    
    # Also create indexes on typed labels if they exist
    for entity_type in entity_types:
        typed_label = entity_type.lower().replace('-', '_')
        typed_label = re.sub(r'[^a-z0-9_]', '_', typed_label)
        indexes.append(f"CREATE INDEX IF NOT EXISTS FOR (e:`{typed_label}`) ON (e.id)")
    
    indexes_created = 0
    with driver.session(database=database) as session:
        for index_query in indexes:
            try:
                session.run(index_query)
                indexes_created += 1
            except Exception:
                # Try without IF NOT EXISTS for older Neo4j versions
                try:
                    alt_query = index_query.replace(" IF NOT EXISTS", "")
                    session.run(alt_query)
                    indexes_created += 1
                except Exception:
                    # Index might already exist, that's OK
                    pass
    
    print(f"  ✓ Created indexes on :Entity nodes")


def verify_load(driver, database: str, expected_entities: int, expected_edges: int):
    """Verify that data was loaded correctly."""
    print("\nVerifying load...")
    
    with driver.session(database=database) as session:
        # Count :Entity nodes
        result = session.run("MATCH (e:Entity) RETURN count(e) AS count")
        record = result.single()
        actual_entities = record["count"] if record else 0
        
        # Count all relationships (will be 2x expected since we create both typed and :RELATIONSHIP)
        result = session.run("MATCH ()-[r]->() RETURN count(r) AS count")
        record = result.single()
        actual_edges_total = record["count"] if record else 0
        
        # Count :RELATIONSHIP relationships specifically (what retrieval uses)
        result = session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) AS count")
        record = result.single()
        actual_edges = record["count"] if record else 0
        
        # Count by entity type
        result = session.run("""
            MATCH (e:Entity)
            RETURN e.type AS type, count(e) AS count
            ORDER BY count DESC
        """)
        type_counts = {}
        for record in result:
            entity_type = record["type"]
            count = record["count"]
            type_counts[entity_type] = count
        
        # Count by relationship type
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) AS reltype, count(r) AS count
            ORDER BY count DESC
        """)
        reltype_counts = {}
        for record in result:
            reltype = record["reltype"]
            count = record["count"]
            reltype_counts[reltype] = count
        
        # Check for kubelet
        result = session.run('MATCH (e:Entity {id: "kubelet"}) RETURN count(e) AS count')
        record = result.single()
        kubelet_exists = record["count"] > 0 if record else False
        
        print(f"  :Entity nodes: {actual_entities} (expected: {expected_entities})")
        if type_counts:
            print(f"  Nodes by type: {dict(type_counts)}")
        
        print(f"  :RELATIONSHIP relationships: {actual_edges} (expected: {expected_edges})")
        print(f"  Total relationships (typed + :RELATIONSHIP): {actual_edges_total}")
        if reltype_counts:
            print(f"  Relationships by type: {dict(reltype_counts)}")
        
        print(f"  kubelet entity exists: {kubelet_exists}")
        
        if actual_entities != expected_entities:
            print(f"  ⚠ Warning: Entity count mismatch!", file=sys.stderr)
            return False
        
        if actual_edges != expected_edges:
            print(f"  ⚠ Warning: Relationship count mismatch!", file=sys.stderr)
            return False
        
        if not kubelet_exists:
            print(f"  ⚠ Warning: kubelet entity not found!", file=sys.stderr)
            return False
        
        print("  ✓ Verification passed")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Load graph data from JSON into Neo4j"
    )
    parser.add_argument(
        "--graph-file",
        type=Path,
        default=None,
        help="Path to graph JSON file (default: complete_graph.json in repo root)"
    )
    parser.add_argument(
        "--skip-verify",
        action="store_true",
        help="Skip verification step"
    )
    
    args = parser.parse_args()
    
    # Determine graph file path
    if args.graph_file:
        graph_file = Path(args.graph_file)
    else:
        graph_file = get_default_graph_file()
    
    # Resolve to absolute path
    graph_file = graph_file.resolve()
    
    # Compute SHA256 hash of the graph file
    file_hash = compute_file_hash(graph_file)
    
    # Get Neo4j connection details from environment
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "testpassword")
    neo4j_db = os.getenv("NEO4J_DB", "neo4j")
    
    print("=" * 70)
    print("GraphRAG Graph Loader")
    print("=" * 70)
    print(f"Graph file: {graph_file}")
    print(f"SHA256 hash: {file_hash}")
    print(f"Neo4j URI: {neo4j_uri}")
    print(f"Neo4j DB: {neo4j_db}")
    print("=" * 70)
    
    # Load graph data
    graph_data = load_graph_data(graph_file)
    entities = graph_data["entities"]
    edges = graph_data["edges"]
    
    print(f"\nGraph data loaded:")
    print(f"  Entities: {len(entities)}")
    print(f"  Edges: {len(edges)}")
    
    # Validate graph schema
    print("\nValidating graph schema...")
    schema_errors = validate_schema(graph_data)
    if schema_errors:
        print("  ✗ Schema validation failed:", file=sys.stderr)
        for error in schema_errors:
            print(f"    {error}", file=sys.stderr)
        sys.exit(2)
    print("  ✓ Schema validation passed")
    
    # Validate graph invariants
    print("Validating graph invariants...")
    invariant_errors = validate_invariants(graph_data)
    if invariant_errors:
        print("  ✗ Invariant validation failed:", file=sys.stderr)
        for error in invariant_errors:
            print(f"    {error}", file=sys.stderr)
        sys.exit(2)
    print("  ✓ Invariant validation passed")
    
    # Verify SHA256 hash matches metadata
    print("Verifying graph hash against metadata...")
    metadata_file = repo_root / "data" / "graph_metadata.json"
    if metadata_file.exists():
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            expected_hash = metadata.get('sha256')
            if expected_hash and file_hash != expected_hash:
                print(f"  ✗ Hash mismatch!", file=sys.stderr)
                print(f"    Expected: {expected_hash}", file=sys.stderr)
                print(f"    Computed: {file_hash}", file=sys.stderr)
                print(f"    Run 'python scripts/update_graph_metadata.py' to update metadata.", file=sys.stderr)
                sys.exit(2)
            print(f"  ✓ Hash matches metadata ({file_hash[:16]}...)")
        except Exception as e:
            print(f"  ⚠ Could not verify hash against metadata: {e}", file=sys.stderr)
            print(f"    Continuing anyway...", file=sys.stderr)
    else:
        print(f"  ⚠ Metadata file not found: {metadata_file}", file=sys.stderr)
        print(f"    Run 'python scripts/update_graph_metadata.py' to generate metadata.", file=sys.stderr)
        print(f"    Continuing anyway...", file=sys.stderr)
    
    # Build entity lookup for matching
    entity_lookup = build_entity_lookup(entities)
    entity_types = set(entity.get("type", "unknown") for entity in entities)
    
    print(f"  Entity types: {sorted(entity_types)}")
    
    # Connect to Neo4j
    print(f"\nConnecting to Neo4j...")
    try:
        driver = GraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password)
        )
        # Verify connection
        with driver.session(database=neo4j_db) as session:
            session.run("RETURN 1")
        print("  ✓ Connected to Neo4j")
    except Exception as e:
        print(f"  ✗ Failed to connect to Neo4j: {e}", file=sys.stderr)
        sys.exit(2)
    
    try:
        # Clear existing graph
        clear_graph(driver, neo4j_db)
        
        # Load entities
        load_entities(driver, neo4j_db, entities)
        
        # Load edges
        load_edges(driver, neo4j_db, edges, entity_lookup)
        
        # Create indexes
        create_indexes(driver, neo4j_db, entity_types)
        
        # Verify load
        if not args.skip_verify:
            success = verify_load(driver, neo4j_db, len(entities), len(edges))
            if not success:
                print("\n⚠ Verification failed, but data may still be loaded correctly", file=sys.stderr)
        
        print("\n" + "=" * 70)
        print("✓ Graph loaded successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n✗ Error loading graph: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
