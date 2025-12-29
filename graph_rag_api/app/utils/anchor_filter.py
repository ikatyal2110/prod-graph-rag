"""
Anchor filtering and precision rules for GraphRAG retrieval.

This module implements deterministic rules to reduce anchor noise while
maintaining retrieval accuracy. Rules are applied after candidate anchor
scoring but before final anchor selection.
"""

from typing import List, Dict, Set, Any
import re


# Failure mode specificity order (more specific = higher priority)
# oom > panic > crash > degradation
FAILURE_MODE_SPECIFICITY = {
    'oom': 4,
    'panic': 3,
    'crash': 2,
    'degradation': 1,
}

# Default specificity for unknown failure modes
DEFAULT_FAILURE_MODE_SPECIFICITY = 0

# Maximum number of failure_mode anchors to keep
MAX_FAILURE_MODE_ANCHORS = 2

# Strong crash indicators (if present, keep crash even if panic exists)
STRONG_CRASH_INDICATORS = {
    'crashloop',
    'crash loop',
    'segfault',
    'segmentation fault',
    'fatal error',
    'core dump',
    'abort',
}

# High-signal concept allowlist (concepts that are specific enough to be useful anchors)
HIGH_SIGNAL_CONCEPTS = {
    'conntrack-management',
    'scheduler-scoring-logic',
    'edge-case-handling',
    'feature-gate-compatibility',
    'api-backward-compatibility',
    'container-lifecycle-management',
    'resource-creation-order',
    'validation-gaps',
    'container-security',
}

# Generic words that should NOT trigger root cause anchoring
GENERIC_ERROR_WORDS = {
    'error',
    'errors',
    'failure',
    'failures',
    'issue',
    'issues',
    'problem',
    'problems',
    'bug',
    'bugs',
}


def filter_failure_modes(
    candidates: List[Dict[str, Any]],
    question: str
) -> List[Dict[str, Any]]:
    """
    Filter failure_mode anchors to reduce noise.
    
    Rules:
    - Keep at most MAX_FAILURE_MODE_ANCHORS failure modes
    - Prefer more specific modes over generic ones
    - If panic is present, drop crash unless query has strong crash indicators
    
    Args:
        candidates: List of candidate anchors (dicts with 'id', 'type', 'score', etc.)
        question: Original question string
        
    Returns:
        Filtered list of failure_mode candidates
    """
    failure_modes = [c for c in candidates if c.get('type') == 'failure_mode']
    other_anchors = [c for c in candidates if c.get('type') != 'failure_mode']
    
    if len(failure_modes) == 0:
        return candidates
    
    # Sort by specificity (higher = more specific)
    question_lower = question.lower()
    has_strong_crash_indicator = any(
        indicator in question_lower for indicator in STRONG_CRASH_INDICATORS
    )
    
    def failure_mode_key(candidate):
        failure_id = candidate['id'].lower()
        specificity = FAILURE_MODE_SPECIFICITY.get(failure_id, DEFAULT_FAILURE_MODE_SPECIFICITY)
        # Use negative for reverse sort (higher specificity first)
        return (-specificity, -candidate.get('final_score', 0))
    
    failure_modes_sorted = sorted(failure_modes, key=failure_mode_key)
    
    # Special rule: if panic is present and crash is also present
    # drop crash unless strong crash indicators are present
    failure_ids = {c['id'].lower() for c in failure_modes_sorted}
    if 'panic' in failure_ids and 'crash' in failure_ids and not has_strong_crash_indicator:
        # Remove crash, keep panic
        failure_modes_sorted = [
            c for c in failure_modes_sorted
            if c['id'].lower() != 'crash'
        ]
    
    # Keep top MAX_FAILURE_MODE_ANCHORS
    filtered_failure_modes = failure_modes_sorted[:MAX_FAILURE_MODE_ANCHORS]
    
    return other_anchors + filtered_failure_modes


def filter_root_causes(
    candidates: List[Dict[str, Any]],
    question: str,
    normalized_tokens: Set[str]
) -> List[Dict[str, Any]]:
    """
    Filter root_cause anchors to reduce false positives.
    
    Rules:
    - Only keep root_cause if:
      a) The canonical ID appears in normalized_tokens (from synonym mapping), OR
      b) The root_cause ID itself appears as a word/phrase in the question
    - Do NOT keep root_cause if it only matches generic error words
    
    Args:
        candidates: List of candidate anchors
        question: Original question string
        normalized_tokens: Set of tokens after normalization (includes canonical IDs)
        
    Returns:
        Filtered list of candidates
    """
    root_causes = [c for c in candidates if c.get('type') == 'root_cause']
    other_anchors = [c for c in candidates if c.get('type') != 'root_cause']
    
    if not root_causes:
        return candidates
    
    question_lower = question.lower()
    filtered_root_causes = []
    
    for candidate in root_causes:
        root_cause_id = candidate['id']
        root_cause_lower = root_cause_id.lower()
        
        # Check if canonical ID is in normalized tokens (from synonym mapping)
        if root_cause_id in normalized_tokens:
            filtered_root_causes.append(candidate)
            continue
        
        # Check if root_cause ID appears as a word/phrase in question
        # Replace hyphens with optional hyphens/spaces for matching
        root_cause_pattern = root_cause_lower.replace('-', '[- ]')
        pattern = r'\b' + re.escape(root_cause_pattern) + r'\b'
        if re.search(pattern, question_lower):
            # Additional check: don't match if it's only generic words
            # For example, "validation-error" should not match just "error"
            root_cause_parts = root_cause_lower.replace('-', ' ').split()
            generic_matches = [part for part in root_cause_parts if part in GENERIC_ERROR_WORDS]
            if len(generic_matches) == len(root_cause_parts):
                # All parts are generic words, reject
                continue
            filtered_root_causes.append(candidate)
            continue
        
        # If we get here, the root_cause was matched through substring/partial matching
        # which is too weak, so we drop it
        pass  # Drop this candidate
    
    return other_anchors + filtered_root_causes


def filter_concepts(
    candidates: List[Dict[str, Any]],
    question: str,
    normalized_tokens: Set[str]
) -> List[Dict[str, Any]]:
    """
    Filter concept anchors to only high-signal concepts.
    
    Rules:
    - Only keep concepts from HIGH_SIGNAL_CONCEPTS allowlist, OR
    - Keep if the concept ID appears exactly in normalized_tokens or question
    
    Args:
        candidates: List of candidate anchors
        question: Original question string
        normalized_tokens: Set of tokens after normalization
        
    Returns:
        Filtered list of candidates
    """
    concepts = [c for c in candidates if c.get('type') == 'concept']
    other_anchors = [c for c in candidates if c.get('type') != 'concept']
    
    if not concepts:
        return candidates
    
    question_lower = question.lower()
    filtered_concepts = []
    
    for candidate in concepts:
        concept_id = candidate['id']
        concept_lower = concept_id.lower()
        
        # Check if in allowlist
        if concept_id in HIGH_SIGNAL_CONCEPTS:
            filtered_concepts.append(candidate)
            continue
        
        # Check if concept ID appears exactly in normalized_tokens
        if concept_id in normalized_tokens:
            filtered_concepts.append(candidate)
            continue
        
        # Check if concept ID appears as exact phrase in question
        pattern = r'\b' + re.escape(concept_lower.replace('-', '[- ]')) + r'\b'
        if re.search(pattern, question_lower):
            filtered_concepts.append(candidate)
            continue
        
        # If not in allowlist and not explicitly matched, drop it
        pass  # Drop this candidate
    
    return other_anchors + filtered_concepts


def apply_anchor_precision_filters(
    candidates: List[Dict[str, Any]],
    question: str,
    normalized_tokens: Set[str]
) -> List[Dict[str, Any]]:
    """
    Apply all precision filters to anchor candidates.
    
    This function applies filtering rules in order:
    1. Filter failure modes (specificity and conflict resolution)
    2. Filter root causes (only explicit matches)
    3. Filter concepts (allowlist only)
    
    Args:
        candidates: List of candidate anchor dictionaries
        question: Original question string
        normalized_tokens: Set of tokens after normalization
        
    Returns:
        Filtered list of candidates
    """
    # Apply filters in order
    filtered = filter_failure_modes(candidates, question)
    filtered = filter_root_causes(filtered, question, normalized_tokens)
    filtered = filter_concepts(filtered, question, normalized_tokens)
    
    return filtered

