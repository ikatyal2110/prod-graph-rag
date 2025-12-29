#!/usr/bin/env python3
"""
Update graph metadata file with current graph statistics.

This script computes metadata from complete_graph.json and writes it to
data/graph_metadata.json in a deterministic format.

Usage:
    python scripts/update_graph_metadata.py          # Update metadata
    python scripts/update_graph_metadata.py --check   # Check if metadata matches
"""

import argparse
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def get_repo_root() -> Path:
    """Get repository root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def compute_file_hash(graph_file: Path) -> str:
    """Compute SHA256 hash of file contents (binary read)."""
    sha256_hash = hashlib.sha256()
    with open(graph_file, 'rb') as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_metadata(graph_file: Path) -> Dict[str, Any]:
    """Compute metadata from graph JSON file."""
    with open(graph_file, 'r', encoding='utf-8') as f:
        graph_data = json.load(f)
    
    entities = graph_data.get('entities', [])
    edges = graph_data.get('edges', [])
    
    # Count nodes by type
    node_type_counts = Counter()
    incident_count = 0
    entity_ids = set()
    
    for entity in entities:
        entity_id = entity.get('id')
        entity_type = entity.get('type')
        
        # Schema validation: check required fields
        if not entity_id:
            raise ValueError("Entity missing 'id' field")
        if not entity_type:
            raise ValueError(f"Entity {entity_id} missing 'type' field")
        if 'attributes' not in entity:
            raise ValueError(f"Entity {entity_id} missing 'attributes' field")
        
        # Check for duplicate IDs
        if entity_id in entity_ids:
            raise ValueError(f"Duplicate entity ID: {entity_id}")
        entity_ids.add(entity_id)
        
        node_type_counts[entity_type] += 1
        if entity_type == 'incident':
            incident_count += 1
    
    # Count relationships by type
    relationship_type_counts = Counter()
    edge_endpoints = set()
    
    for edge in edges:
        edge_from = edge.get('from')
        edge_to = edge.get('to')
        edge_type = edge.get('type')
        
        # Schema validation: check required fields
        if not edge_from:
            raise ValueError("Edge missing 'from' field")
        if not edge_to:
            raise ValueError("Edge missing 'to' field")
        if not edge_type:
            raise ValueError("Edge missing 'type' field")
        
        # Check endpoints exist
        if edge_from not in entity_ids:
            raise ValueError(f"Edge references non-existent entity: {edge_from}")
        if edge_to not in entity_ids:
            raise ValueError(f"Edge references non-existent entity: {edge_to}")
        
        relationship_type_counts[edge_type] += 1
        edge_endpoints.add((edge_from, edge_to, edge_type))
    
    # Compute SHA256 hash
    sha256 = compute_file_hash(graph_file)
    
    # Build metadata with deterministic key ordering
    metadata = {
        "graph_version": "1.0.0",  # Can be updated manually if needed
        "created_at": datetime.utcnow().isoformat() + "Z",
        "sha256": sha256,
        "incident_count": incident_count,
        "node_count": len(entities),
        "edge_count": len(edges),
        "node_type_counts": dict(sorted(node_type_counts.items())),
        "relationship_type_counts": dict(sorted(relationship_type_counts.items()))
    }
    
    return metadata


def write_metadata(metadata: Dict[str, Any], metadata_file: Path):
    """Write metadata to file with deterministic formatting."""
    # Ensure parent directory exists
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with deterministic formatting (sorted keys, no trailing whitespace)
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write('\n')  # Trailing newline for POSIX compliance


def diff_metadata(old: Dict[str, Any], new: Dict[str, Any]) -> list:
    """Generate diff-style summary of metadata differences."""
    diffs = []
    
    for key in sorted(set(old.keys()) | set(new.keys())):
        old_val = old.get(key)
        new_val = new.get(key)
        
        if old_val != new_val:
            if key in old and key in new:
                diffs.append(f"  {key}: {old_val} -> {new_val}")
            elif key in old:
                diffs.append(f"  {key}: {old_val} -> (removed)")
            else:
                diffs.append(f"  {key}: (added) -> {new_val}")
    
    return diffs


def main():
    parser = argparse.ArgumentParser(
        description="Update or check graph metadata"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if metadata matches computed values (exit non-zero if mismatch)"
    )
    parser.add_argument(
        "--graph-file",
        type=Path,
        default=None,
        help="Path to graph JSON file (default: repo_root/complete_graph.json)"
    )
    parser.add_argument(
        "--metadata-file",
        type=Path,
        default=None,
        help="Path to metadata JSON file (default: repo_root/data/graph_metadata.json)"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    repo_root = get_repo_root()
    graph_file = args.graph_file or (repo_root / "complete_graph.json")
    metadata_file = args.metadata_file or (repo_root / "data" / "graph_metadata.json")
    
    # Validate graph file exists
    if not graph_file.exists():
        print(f"Error: Graph file not found: {graph_file}", file=sys.stderr)
        sys.exit(2)
    
    try:
        # Compute metadata from graph
        computed_metadata = compute_metadata(graph_file)
        
        if args.check:
            # Check mode: compare with existing metadata
            if not metadata_file.exists():
                print(f"Error: Metadata file not found: {metadata_file}", file=sys.stderr)
                print("Run without --check to generate metadata file.", file=sys.stderr)
                sys.exit(1)
            
            with open(metadata_file, 'r', encoding='utf-8') as f:
                existing_metadata = json.load(f)
            
            # Compare (ignore created_at timestamp)
            computed_for_compare = computed_metadata.copy()
            existing_for_compare = existing_metadata.copy()
            computed_for_compare.pop('created_at', None)
            existing_for_compare.pop('created_at', None)
            
            if computed_for_compare != existing_for_compare:
                print("Error: Metadata mismatch!", file=sys.stderr)
                print("\nDifferences:", file=sys.stderr)
                diffs = diff_metadata(existing_for_compare, computed_for_compare)
                for diff in diffs:
                    print(diff, file=sys.stderr)
                sys.exit(1)
            else:
                print("Metadata matches computed values.")
                sys.exit(0)
        else:
            # Update mode: write metadata
            write_metadata(computed_metadata, metadata_file)
            print(f"Metadata written to: {metadata_file}")
            print(f"  SHA256: {computed_metadata['sha256']}")
            print(f"  Nodes: {computed_metadata['node_count']}")
            print(f"  Edges: {computed_metadata['edge_count']}")
            print(f"  Incidents: {computed_metadata['incident_count']}")
            sys.exit(0)
            
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

