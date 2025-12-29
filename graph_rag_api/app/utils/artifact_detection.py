"""Artifact detection utilities"""

from typing import Set, Optional


# Known artifact IDs from the graph (hardcoded for deterministic matching)
# This list should be kept in sync with the graph data
KNOWN_ARTIFACT_IDS = {
    'containermap',
    'containermap.add',
    'servicetoref',
    'ipallocator.go',
    'iptoallocation',
    'vishvananda/netlink',
    'conntrack_linux.go',
    'conntrack-table',
    'ipaddress',
}

# Alternative forms that might appear in queries (case-insensitive matching)
ARTIFACT_VARIANTS = {
    'containerMap': 'containermap',
    'ContainerMap': 'containermap',
    'ContainerMap.Add': 'containermap.add',
    'containerMap.Add': 'containermap.add',
    'serviceToRef': 'servicetoref',
    'ServiceToRef': 'servicetoref',
    'IPAllocator.go': 'ipallocator.go',
    'ipAllocator.go': 'ipallocator.go',
    'IPToAllocation': 'iptoallocation',
    'ipToAllocation': 'iptoallocation',
}


def mentions_artifact(question: str, artifact_ids: Optional[Set[str]] = None) -> bool:
    """
    Check if a question explicitly mentions a known artifact token.
    
    Args:
        question: User question string
        artifact_ids: Optional set of artifact IDs to check against.
                     If None, uses KNOWN_ARTIFACT_IDS
        
    Returns:
        True if question contains an explicit artifact token, False otherwise
    """
    if artifact_ids is None:
        artifact_ids = KNOWN_ARTIFACT_IDS
    
    question_lower = question.lower()
    
    # Special handling: "container map" (with space) should match "containermap" artifact
    if 'container map' in question_lower and 'containermap' in artifact_ids:
        return True
    
    # Check for exact artifact ID matches (case-insensitive)
    for artifact_id in artifact_ids:
        artifact_id_lower = artifact_id.lower()
        # Use word boundaries or exact substring match for compound identifiers
        if artifact_id_lower in question_lower:
            # Also check exact match or followed by valid separator
            idx = question_lower.find(artifact_id_lower)
            if idx >= 0:
                # Check if it's followed by a dot (method call) or is a standalone word
                remaining = question_lower[idx + len(artifact_id_lower):]
                if not remaining or remaining[0] in ['.', ' ', ',', ';', '(', ')', '\n', '\t']:
                    return True
    
    # Also check variant forms
    for variant, canonical in ARTIFACT_VARIANTS.items():
        if variant.lower() in question_lower or variant in question:
            return True
    
    return False


def get_mentioned_artifacts(question: str, artifact_ids: Optional[Set[str]] = None) -> Set[str]:
    """
    Get the set of artifact IDs explicitly mentioned in the question.
    
    Args:
        question: User question string
        artifact_ids: Optional set of artifact IDs to check against
        
    Returns:
        Set of artifact IDs found in the question
    """
    if artifact_ids is None:
        artifact_ids = KNOWN_ARTIFACT_IDS
    
    question_lower = question.lower()
    mentioned = set()
    
    # Check for exact artifact ID matches
    for artifact_id in artifact_ids:
        artifact_id_lower = artifact_id.lower()
        if artifact_id_lower in question_lower:
            idx = question_lower.find(artifact_id_lower)
            if idx >= 0:
                remaining = question_lower[idx + len(artifact_id_lower):]
                if not remaining or remaining[0] in ['.', ' ', ',', ';', '(', ')', '\n', '\t']:
                    mentioned.add(artifact_id)
    
    # Also check variant forms and map to canonical IDs
    for variant, canonical in ARTIFACT_VARIANTS.items():
        if variant.lower() in question_lower or variant in question:
            # Find the canonical ID
            for artifact_id in artifact_ids:
                if artifact_id.lower() == canonical.lower():
                    mentioned.add(artifact_id)
    
    return mentioned

