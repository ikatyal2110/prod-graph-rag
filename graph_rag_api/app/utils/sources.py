"""Source resolution utility for graph provenance"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

# Cache for sources loaded from graph JSON
_sources_cache: Optional[Dict[str, Dict[str, Any]]] = None


def load_sources(graph_file: Optional[Path] = None) -> Dict[str, Dict[str, Any]]:
    """
    Load sources from graph JSON file.
    
    Args:
        graph_file: Path to graph JSON file. If None, uses default location.
        
    Returns:
        Dictionary mapping source_id -> source object
    """
    global _sources_cache
    
    if _sources_cache is not None:
        return _sources_cache
    
    if graph_file is None:
        # Default: look for complete_graph.json in repo root
        script_dir = Path(__file__).parent
        repo_root = script_dir.parent.parent.parent
        graph_file = repo_root / "complete_graph.json"
    
    if not graph_file.exists():
        # If graph file doesn't exist, return empty dict
        _sources_cache = {}
        return _sources_cache
    
    try:
        with open(graph_file, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        sources = graph_data.get('sources', [])
        _sources_cache = {source.get('id'): source for source in sources if source.get('id')}
        return _sources_cache
    except Exception:
        # If loading fails, return empty dict
        _sources_cache = {}
        return _sources_cache


def resolve_sources(evidence_refs: List[str]) -> List[Dict[str, Any]]:
    """
    Resolve evidence_refs to source objects.
    
    Args:
        evidence_refs: List of source IDs
        
    Returns:
        List of source objects (id, kind, title, url, ref)
    """
    sources = load_sources()
    resolved = []
    for ref_id in evidence_refs:
        if ref_id in sources:
            source = sources[ref_id]
            resolved.append({
                "id": source.get("id"),
                "kind": source.get("kind"),
                "title": source.get("title"),
                "url": source.get("url"),
                "ref": source.get("ref")
            })
    return resolved


def clear_cache():
    """Clear the sources cache (useful for testing)."""
    global _sources_cache
    _sources_cache = None

