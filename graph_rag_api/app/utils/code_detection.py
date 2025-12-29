"""Code query detection utilities"""

import re
from typing import Set


def is_code_query(question: str) -> bool:
    """
    Determine if a question is code-related using deterministic heuristics.
    
    Returns True if the question contains explicit code/stacktrace indicators.
    
    Args:
        question: User question string
        
    Returns:
        True if question appears to be code-related, False otherwise
    """
    question_lower = question.lower()
    
    # Check for stack trace / panic indicators
    stack_trace_indicators = [
        "stack trace",
        "traceback",
        "panic at",
        "segfault",
        "nil pointer",
        "fatal error",
        "panic:",
        "runtime error",
    ]
    if any(indicator in question_lower for indicator in stack_trace_indicators):
        return True
    
    # Check for file path patterns like "/path/to/file.go" or "file.yaml"
    file_path_pattern = r'[\/\\][\w\/\.\-]+\.(go|yaml|yml|json|py|js|ts|java|cpp|cc|h|hpp|rs)$'
    if re.search(file_path_pattern, question):
        return True
    
    # Check for file extensions in the text
    file_extensions = ['.go', '.yaml', '.yml', '.json', '.py', '.js', '.ts', '.java', '.cpp', '.cc', '.h', '.hpp', '.rs']
    if any(ext in question for ext in file_extensions):
        return True
    
    # Check for code symbol patterns
    
    # CamelCase pattern: matches identifiers like "ContainerMap", "ServiceToRef"
    # But be careful: single CamelCase might be a component name (e.g., "kubelet", "ContainerMap")
    camel_case_pattern = r'\b[A-Z][a-z]+[A-Za-z0-9]*\b'
    camel_case_matches = re.findall(camel_case_pattern, question)
    
    if camel_case_matches:
        # Filter out known component names to avoid false positives
        known_components = {
            'kubelet', 'kube-apiserver', 'kube-scheduler', 'kube-proxy',
            'kube-controller-manager', 'cloud-controller-manager',
            'horizontal-pod-autoscaler', 'container-runtime'
        }
        # Check if matches are known components (case-insensitive)
        code_like_camelcase = [
            m for m in camel_case_matches
            if m.lower() not in known_components
        ]
        
        if len(code_like_camelcase) >= 2:  # At least 2 code-like CamelCase identifiers
            return True
        # Single CamelCase: check if it looks like code
        # If it's followed by a dot or paren, it's likely code
        for match in camel_case_matches:
            idx = question.find(match)
            if idx >= 0:
                # Check if followed by dot (method call) or paren (function call)
                remaining = question[idx + len(match):].strip()
                if remaining.startswith('.') or remaining.startswith('('):
                    return True
    
    # Dotted symbol pattern: matches "ContainerMap.Add", "serviceToRef.method"
    dotted_symbol_pattern = r'\b[a-zA-Z_][\w]*\.[A-Za-z_][\w]*\b'
    if re.search(dotted_symbol_pattern, question):
        return True
    
    # Function call pattern: matches "function(" or "method("
    function_call_pattern = r'\b\w+\s*\('
    if re.search(function_call_pattern, question):
        return True
    
    # Check for code-related keywords
    code_keywords = [
        "function",
        "method",
        "struct",
        "file",
        "line",
        "commit",
        "pr",
        "diff",
        "code",
        "implementation",
        "package",
        "import",
        "variable",
        "constant",
    ]
    if any(keyword in question_lower for keyword in code_keywords):
        return True
    
    return False

