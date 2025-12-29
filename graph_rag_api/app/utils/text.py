"""Text processing utilities"""

import re
from typing import List, Set

# Banned tokens: overly generic Kubernetes terms that match too many entities
BANNED_TOKENS = {
    "kube", "kubernetes", "cluster", "clusters", "node", "nodes",
    "pod", "pods", "control", "plane", "component", "components"
}

# Exception tokens: specific component names that should not be banned
ALLOWED_TOKENS = {
    "kubelet", "kube-scheduler", "kube-proxy", "kube-apiserver",
    "kube-controller-manager"
}


def tokenize_question(question: str) -> Set[str]:
    """
    Tokenize a question into a set of searchable tokens.
    
    Simple tokenization: lowercase, split on whitespace/punctuation,
    drop tokens < 4 chars, filter banned generic terms.
    
    Args:
        question: Input question string
        
    Returns:
        Set of token strings (normalized, lowercase, filtered)
    """
    # Lowercase and split on whitespace and punctuation
    tokens = re.split(r'[\s\W_]+', question.lower())
    
    # Filter: keep tokens with at least 4 characters
    filtered_tokens = {token for token in tokens if len(token) >= 4}
    
    # Remove banned tokens, but keep allowed exceptions
    # Check if question contains allowed compound terms first
    question_lower = question.lower()
    final_tokens = set()
    
    # First, check for allowed compound terms in the question
    for allowed in ALLOWED_TOKENS:
        allowed_normalized = allowed.lower().replace('-', '').replace('_', '')
        if allowed_normalized in question_lower or allowed.lower() in question_lower:
            final_tokens.add(allowed_normalized)
    
    # Then process individual tokens
    for token in filtered_tokens:
        # Skip if token is in banned list
        if token in BANNED_TOKENS:
            continue
        
        # Skip if this token is already covered by an allowed compound term
        covered_by_allowed = False
        for allowed in ALLOWED_TOKENS:
            if token in allowed.lower().replace('-', '').replace('_', ''):
                covered_by_allowed = True
                break
        
        if not covered_by_allowed:
            final_tokens.add(token)
    
    return final_tokens
