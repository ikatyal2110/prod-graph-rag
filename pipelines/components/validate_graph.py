#!/usr/bin/env python3
"""
Container component for graph validation.

This script runs graph validation inside a container.
It expects the repo workspace to be mounted at /workspace.
"""

import json
import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, "/workspace")

from graph.validate_graph import validate_schema, validate_invariants


def main():
    """Run graph validation."""
    graph_file = Path("/workspace/complete_graph.json")
    
    if not graph_file.exists():
        print(f"Error: Graph file not found: {graph_file}", file=sys.stderr)
        sys.exit(1)
    
    # Load graph data
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading graph file: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Import validate_graph function if available, otherwise use individual functions
    try:
        from graph.validate_graph import validate_graph
        schema_errors, invariant_errors = validate_graph(graph_data)
    except ImportError:
        # Fallback to individual functions
        schema_errors = validate_schema(graph_data)
        invariant_errors = validate_invariants(graph_data)
    
    # Validate schema
    print("Validating graph schema...")
    if schema_errors:
        print("Schema validation failed:", file=sys.stderr)
        for error in schema_errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)
    print("✓ Schema validation passed")
    
    # Validate invariants
    print("Validating graph invariants...")
    if invariant_errors:
        print("Invariant validation failed:", file=sys.stderr)
        for error in invariant_errors:
            print(f"  {error}", file=sys.stderr)
        sys.exit(1)
    print("✓ Invariant validation passed")
    
    print("Validation passed!")
    sys.exit(0)


if __name__ == "__main__":
    main()

