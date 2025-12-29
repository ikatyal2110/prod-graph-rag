"""
Deterministic synonym normalization for GraphRAG queries.

This module maps common phrasing variants to canonical graph entity IDs
to improve anchor extraction accuracy without using embeddings or LLMs.

All normalization is deterministic and uses substring matching with word boundaries
to avoid over-matching partial words.
"""

import re
from typing import Set, List


# Canonical synonym mappings
# Format: {canonical_id: [variants...]}
SYNONYM_MAPPINGS = {
    # Root causes
    "division-by-zero": [
        "divide by 0",
        "divide-by-0",
        "division by 0",
        "divide by zero",
        "div by 0",
        "division by zero",
        "integer divide by zero",
    ],
    "unsynchronized-concurrent-access": [
        "concurrent writes",
        "concurrent map write",
        "concurrent map writes",
        "race condition",
        "simultaneous map modifications",
        "concurrent map access",
    ],
    "unbounded-memory-growth": [
        "out of memory",
        "oomkilled",
        "oom kill",
        "memory blowup",
        "memory spike",
        "excessive memory",
        "memory leak",
        "unbounded memory growth",
    ],
    
    # Components
    "kube-scheduler": [
        "scheduler",
        "kube scheduler",
        "kube-scheduler",
    ],
    "kubelet": [
        "node agent",
        "kubelet",
    ],
    "kube-proxy": [
        "proxy",
        "kube-proxy",
        "network proxy",
    ],
    "kube-apiserver": [
        "api server",
        "kube apiserver",
        "kube-apiserver",
        "apiserver",
    ],
    
    # Failure modes
    "panic": [
        "panic",
        "crashes",
        "crash",
        "crashed",
    ],
    "crash": [
        "crash",
        "crashes",
        "crashed",
        "fatal error",
    ],
    "oom": [
        "oom",
        "out of memory",
        "oomkilled",
        "oom killed",
    ],
    "degradation": [
        "degradation",
        "performance degradation",
    ],
    
    # Triggers/Concepts
    "conntrack-management": [
        "conntrack cleanup",
        "conntrack",
        "connection tracking",
        "connection state",
    ],
    "udp-endpoint-change": [
        "udp endpoint change",
        "udp endpoint update",
        "udp port change",
    ],
}


def normalize_question(question: str) -> str:
    """
    Normalize a question string by replacing synonyms with canonical IDs.
    
    This function performs deterministic string replacement to map common
    phrasing variants to canonical graph entity IDs.
    
    Args:
        question: Raw question string
        
    Returns:
        Normalized question string with canonical IDs inserted
    """
    # Lowercase for matching
    normalized = question.lower()
    
    # Apply synonym mappings in order (longest variants first to avoid partial matches)
    # Sort by length descending to match longer phrases first
    for canonical_id, variants in SYNONYM_MAPPINGS.items():
        sorted_variants = sorted(variants, key=len, reverse=True)
        for variant in sorted_variants:
            # Use word boundaries to avoid partial word matches
            # Replace with canonical_id (keeping original case pattern if needed)
            pattern = r'\b' + re.escape(variant) + r'\b'
            if re.search(pattern, normalized):
                # Replace variant with canonical_id
                normalized = re.sub(pattern, canonical_id, normalized)
    
    # Preserve original case structure for readability, but normalization is done
    # The normalized version will be used for tokenization
    return normalized


def extract_canonical_tokens(text: str) -> Set[str]:
    """
    Extract canonical tokens from text using synonym mappings.
    
    This function identifies which canonical IDs are present in the text
    by checking for their variants.
    
    Args:
        text: Input text string
        
    Returns:
        Set of canonical IDs found in the text
    """
    text_lower = text.lower()
    found_canonical = set()
    
    # Check each canonical ID and its variants
    for canonical_id, variants in SYNONYM_MAPPINGS.items():
        # Check if canonical_id itself is present
        pattern = r'\b' + re.escape(canonical_id) + r'\b'
        if re.search(pattern, text_lower):
            found_canonical.add(canonical_id)
            continue
        
        # Check variants
        for variant in variants:
            pattern = r'\b' + re.escape(variant) + r'\b'
            if re.search(pattern, text_lower):
                found_canonical.add(canonical_id)
                break  # Found one variant, no need to check others
    
    return found_canonical


def normalize_and_enhance_tokens(tokens: Set[str], question: str) -> Set[str]:
    """
    Normalize tokens and add canonical IDs based on question content.
    
    This function takes a set of tokens and enhances them with canonical IDs
    found in the original question through synonym matching.
    
    Args:
        tokens: Set of extracted tokens
        question: Original question string
        
    Returns:
        Enhanced set of tokens including canonical IDs
    """
    # Start with original tokens
    enhanced = set(tokens)
    
    # Extract canonical IDs from question (this does the synonym matching)
    canonical_ids = extract_canonical_tokens(question)
    enhanced.update(canonical_ids)
    
    # Also check if any existing tokens match canonical IDs directly
    for token in tokens:
        # Check if token is already a canonical ID
        if token in SYNONYM_MAPPINGS:
            enhanced.add(token)
            continue
        
        # Check if token matches any canonical ID (already normalized)
        # This helps when tokenization extracts the canonical form
        for canonical_id in SYNONYM_MAPPINGS.keys():
            if token == canonical_id or canonical_id.replace('-', '').replace('_', '') == token.replace('-', '').replace('_', ''):
                enhanced.add(canonical_id)
                break
    
    return enhanced

