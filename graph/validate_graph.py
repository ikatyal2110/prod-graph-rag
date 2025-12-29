#!/usr/bin/env python3
"""
Graph validation module.

Provides schema and invariant validation for the graph JSON structure.
"""

from typing import Dict, List, Any, Set
from collections import defaultdict

# Edge types that require provenance (evidence_refs)
REQUIRED_PROVENANCE_EDGE_TYPES = ['AFFECTS', 'EXHIBITS', 'CAUSED_BY', 'TRIGGERED_BY', 'USES']


def validate_schema(graph: Dict[str, Any]) -> List[str]:
    """
    Validate graph schema.
    
    Schema rules:
    - Unique node IDs
    - Required fields: id, type, attributes
    - Required edge fields: source, target, type (note: graph uses 'from'/'to')
    - All edge endpoints must exist
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    entities = graph.get('entities', [])
    edges = graph.get('edges', [])
    
    # Build entity lookup
    entity_ids = set()
    entity_by_id = {}
    
    for idx, entity in enumerate(entities):
        entity_id = entity.get('id')
        entity_type = entity.get('type')
        
        # Check required fields
        if not entity_id:
            errors.append(f"Entity at index {idx} missing 'id' field")
            continue
        
        if not entity_type:
            errors.append(f"Entity '{entity_id}' missing 'type' field")
            continue
        
        if 'attributes' not in entity:
            errors.append(f"Entity '{entity_id}' missing 'attributes' field")
            continue
        
        # Check for duplicate IDs
        if entity_id in entity_ids:
            errors.append(f"Duplicate entity ID: '{entity_id}'")
        else:
            entity_ids.add(entity_id)
            entity_by_id[entity_id] = entity
    
    # Validate edges
    for idx, edge in enumerate(edges):
        edge_from = edge.get('from')
        edge_to = edge.get('to')
        edge_type = edge.get('type')
        
        # Check required fields
        if not edge_from:
            errors.append(f"Edge at index {idx} missing 'from' field")
            continue
        
        if not edge_to:
            errors.append(f"Edge at index {idx} missing 'to' field")
            continue
        
        if not edge_type:
            errors.append(f"Edge at index {idx} missing 'type' field")
            continue
        
        # Check endpoints exist
        if edge_from not in entity_ids:
            errors.append(f"Edge at index {idx} references non-existent entity: '{edge_from}'")
        
        if edge_to not in entity_ids:
            errors.append(f"Edge at index {idx} references non-existent entity: '{edge_to}'")
    
    # Validate sources if present
    sources = graph.get('sources', [])
    if sources:
        source_ids = set()
        for idx, source in enumerate(sources):
            source_id = source.get('id')
            if not source_id:
                errors.append(f"Source at index {idx} missing 'id' field")
                continue
            if source_id in source_ids:
                errors.append(f"Duplicate source ID: '{source_id}'")
            else:
                source_ids.add(source_id)
        
        # Validate evidence_refs in edges
        # Build incident IDs set
        incident_ids = {e.get('id') for e in entities if e.get('type') == 'incident'}
        
        for idx, edge in enumerate(edges):
            edge_from = edge.get('from')
            edge_to = edge.get('to')
            edge_type = edge.get('type')
            edge_attrs = edge.get('attributes', {})
            evidence_refs = edge_attrs.get('evidence_refs', [])
            
            # Check if this edge type requires provenance AND edge is from an incident
            # (edges from incidents represent factual claims about incidents)
            if edge_type in REQUIRED_PROVENANCE_EDGE_TYPES and edge_from in incident_ids:
                if not evidence_refs:
                    errors.append(f"Edge ({edge_from}, {edge_type}, {edge_to}) missing required evidence_refs")
                elif not isinstance(evidence_refs, list):
                    errors.append(f"Edge ({edge_from}, {edge_type}, {edge_to}) evidence_refs must be a list")
                elif len(evidence_refs) == 0:
                    errors.append(f"Edge ({edge_from}, {edge_type}, {edge_to}) evidence_refs must be non-empty")
                else:
                    # Check all evidence_refs point to valid sources
                    for ref in evidence_refs:
                        if ref not in source_ids:
                            errors.append(f"Edge ({edge_from}, {edge_type}, {edge_to}) references non-existent source: '{ref}'")
            
            # Also check that any evidence_refs that exist point to valid sources (even if not required)
            if evidence_refs:
                for ref in evidence_refs:
                    if ref not in source_ids:
                        errors.append(f"Edge ({edge_from}, {edge_type}, {edge_to}) references non-existent source: '{ref}'")
    
    return errors


def validate_invariants(graph: Dict[str, Any]) -> List[str]:
    """
    Validate graph invariants.
    
    Invariants:
    A) Every incident has exactly 1 EXHIBITS -> failure_mode
    B) Every incident has exactly 1 CAUSED_BY -> root_cause
    C) Every incident has >=1 AFFECTS -> component
    D) CAUSED_BY target must be type root_cause (not concept)
    E) TRIGGERED_BY target must be type trigger
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    entities = graph.get('entities', [])
    edges = graph.get('edges', [])
    
    # Build entity lookup
    entity_by_id = {}
    incident_ids = set()
    
    for entity in entities:
        entity_id = entity.get('id')
        entity_type = entity.get('type')
        entity_by_id[entity_id] = entity
        if entity_type == 'incident':
            incident_ids.add(entity_id)
    
    # Build edge index: incident_id -> list of edges
    incident_edges = defaultdict(list)
    for edge in edges:
        edge_from = edge.get('from')
        edge_to = edge.get('to')
        edge_type = edge.get('type')
        
        if edge_from in incident_ids:
            incident_edges[edge_from].append({
                'type': edge_type,
                'to': edge_to
            })
    
    # Invariant A: Every incident has exactly 1 EXHIBITS -> failure_mode
    for incident_id in incident_ids:
        exhibits_edges = [
            e for e in incident_edges[incident_id]
            if e['type'] == 'EXHIBITS'
        ]
        
        if len(exhibits_edges) == 0:
            errors.append(f"Incident '{incident_id}' has no EXHIBITS -> failure_mode edge")
        elif len(exhibits_edges) > 1:
            errors.append(f"Incident '{incident_id}' has {len(exhibits_edges)} EXHIBITS edges (expected exactly 1)")
        else:
            # Check target is a failure_mode
            target_id = exhibits_edges[0]['to']
            target_entity = entity_by_id.get(target_id)
            if target_entity and target_entity.get('type') != 'failure_mode':
                errors.append(f"Incident '{incident_id}' EXHIBITS edge targets '{target_id}' which is type '{target_entity.get('type')}' (expected 'failure_mode')")
    
    # Invariant B: Every incident has exactly 1 CAUSED_BY -> root_cause
    for incident_id in incident_ids:
        caused_by_edges = [
            e for e in incident_edges[incident_id]
            if e['type'] == 'CAUSED_BY'
        ]
        
        if len(caused_by_edges) == 0:
            errors.append(f"Incident '{incident_id}' has no CAUSED_BY -> root_cause edge")
        elif len(caused_by_edges) > 1:
            errors.append(f"Incident '{incident_id}' has {len(caused_by_edges)} CAUSED_BY edges (expected exactly 1)")
        else:
            # Invariant D: CAUSED_BY target must be type root_cause
            target_id = caused_by_edges[0]['to']
            target_entity = entity_by_id.get(target_id)
            if not target_entity:
                errors.append(f"Incident '{incident_id}' CAUSED_BY edge targets non-existent entity '{target_id}'")
            elif target_entity.get('type') != 'root_cause':
                errors.append(f"Incident '{incident_id}' CAUSED_BY edge targets '{target_id}' which is type '{target_entity.get('type')}' (expected 'root_cause')")
    
    # Invariant C: Every incident has >=1 AFFECTS -> component
    for incident_id in incident_ids:
        affects_edges = [
            e for e in incident_edges[incident_id]
            if e['type'] == 'AFFECTS'
        ]
        
        if len(affects_edges) == 0:
            errors.append(f"Incident '{incident_id}' has no AFFECTS -> component edge")
        else:
            # Check all targets are components
            for edge in affects_edges:
                target_id = edge['to']
                target_entity = entity_by_id.get(target_id)
                if target_entity and target_entity.get('type') != 'component':
                    errors.append(f"Incident '{incident_id}' AFFECTS edge targets '{target_id}' which is type '{target_entity.get('type')}' (expected 'component')")
    
    # Invariant E: TRIGGERED_BY target must be type trigger
    for edge in edges:
        if edge.get('type') == 'TRIGGERED_BY':
            target_id = edge.get('to')
            target_entity = entity_by_id.get(target_id)
            if not target_entity:
                errors.append(f"TRIGGERED_BY edge from '{edge.get('from')}' targets non-existent entity '{target_id}'")
            elif target_entity.get('type') != 'trigger':
                errors.append(f"TRIGGERED_BY edge from '{edge.get('from')}' targets '{target_id}' which is type '{target_entity.get('type')}' (expected 'trigger')")
    
    return errors


def validate_graph(graph: Dict[str, Any]) -> tuple[List[str], List[str]]:
    """
    Validate graph schema and invariants.
    
    Returns:
        Tuple of (schema_errors, invariant_errors)
    """
    schema_errors = validate_schema(graph)
    invariant_errors = validate_invariants(graph)
    return schema_errors, invariant_errors


if __name__ == "__main__":
    """CLI entry point for validation."""
    import argparse
    import json
    import sys
    from pathlib import Path
    
    parser = argparse.ArgumentParser(
        description="Validate graph JSON file"
    )
    parser.add_argument(
        "graph_file",
        type=Path,
        help="Path to graph JSON file"
    )
    
    args = parser.parse_args()
    
    if not args.graph_file.exists():
        print(f"Error: Graph file not found: {args.graph_file}", file=sys.stderr)
        sys.exit(2)
    
    try:
        with open(args.graph_file, 'r', encoding='utf-8') as f:
            graph = json.load(f)
        
        schema_errors, invariant_errors = validate_graph(graph)
        
        if schema_errors or invariant_errors:
            print("Validation failed!", file=sys.stderr)
            
            if schema_errors:
                print("\nSchema errors:", file=sys.stderr)
                for error in schema_errors:
                    print(f"  {error}", file=sys.stderr)
            
            if invariant_errors:
                print("\nInvariant errors:", file=sys.stderr)
                for error in invariant_errors:
                    print(f"  {error}", file=sys.stderr)
            
            sys.exit(1)
        else:
            print("Validation passed!")
            sys.exit(0)
            
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error: Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(2)

