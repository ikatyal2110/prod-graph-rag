#!/usr/bin/env python3
"""
Regression test for failure_mode anchor precision.

Tests that failure_mode anchoring is precise and deterministic:
- "panic" only when explicitly present (or panic syntax)
- "crash" for crash-related phrasing
- No false positives where "panic" is emitted for crash queries
"""

import sys
import os
# Add parent directory (graph_rag_api) to path
script_dir = os.path.dirname(os.path.abspath(__file__))
graph_rag_api_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, graph_rag_api_dir)

from app.utils.normalize import extract_canonical_tokens
from app.utils.anchor_filter import filter_failure_modes


def test_kubelet_crash_query():
    """
    Test: "kubelet crash concurrent map writes containerMap"
    
    Expected:
    - anchors must include failure_mode "crash"
    - anchors must NOT include failure_mode "panic"
    """
    query = "kubelet crash concurrent map writes containerMap"
    
    # Extract canonical tokens (what normalization would find)
    canonical_tokens = extract_canonical_tokens(query)
    
    # Simulate candidate anchors
    candidates = [
        {'id': 'kubelet', 'type': 'component', 'final_score': 20},
        {'id': 'crash', 'type': 'failure_mode', 'final_score': 15},
        {'id': 'panic', 'type': 'failure_mode', 'final_score': 14},  # Should be filtered out
        {'id': 'unsynchronized-concurrent-access', 'type': 'root_cause', 'final_score': 12},
    ]
    
    # Apply failure mode filter
    filtered = filter_failure_modes(candidates, query)
    failure_modes = [c for c in filtered if c.get('type') == 'failure_mode']
    failure_mode_ids = [c['id'] for c in failure_modes]
    
    print(f"Query: {query}")
    print(f"  Canonical tokens: {canonical_tokens}")
    print(f"  Failure modes after filtering: {failure_mode_ids}")
    
    # Assertions
    assert 'crash' in failure_mode_ids, f"Should include 'crash', got {failure_mode_ids}"
    assert 'panic' not in failure_mode_ids, f"Should NOT include 'panic', got {failure_mode_ids}"
    
    print("  ✓ Test passed: crash included, panic excluded")
    return True


def test_kube_scheduler_panic_query():
    """
    Test: "kube-scheduler panic divide by zero"
    
    Expected:
    - anchors must include failure_mode "panic"
    """
    query = "kube-scheduler panic divide by zero"
    
    # Extract canonical tokens
    canonical_tokens = extract_canonical_tokens(query)
    
    # Simulate candidate anchors
    candidates = [
        {'id': 'kube-scheduler', 'type': 'component', 'final_score': 20},
        {'id': 'panic', 'type': 'failure_mode', 'final_score': 15},
        {'id': 'crash', 'type': 'failure_mode', 'final_score': 14},  # Should be filtered out
        {'id': 'division-by-zero', 'type': 'root_cause', 'final_score': 12},
    ]
    
    # Apply failure mode filter
    filtered = filter_failure_modes(candidates, query)
    failure_modes = [c for c in filtered if c.get('type') == 'failure_mode']
    failure_mode_ids = [c['id'] for c in failure_modes]
    
    print(f"Query: {query}")
    print(f"  Canonical tokens: {canonical_tokens}")
    print(f"  Failure modes after filtering: {failure_mode_ids}")
    
    # Assertions
    assert 'panic' in failure_mode_ids, f"Should include 'panic', got {failure_mode_ids}"
    
    print("  ✓ Test passed: panic included")
    return True


def test_panic_with_colon():
    """
    Test: "kube-scheduler panic: integer divide by zero"
    
    Expected:
    - anchors must include failure_mode "panic" (matches panic: pattern)
    """
    query = "kube-scheduler panic: integer divide by zero"
    
    canonical_tokens = extract_canonical_tokens(query)
    
    candidates = [
        {'id': 'kube-scheduler', 'type': 'component', 'final_score': 20},
        {'id': 'panic', 'type': 'failure_mode', 'final_score': 15},
        {'id': 'crash', 'type': 'failure_mode', 'final_score': 14},
    ]
    
    filtered = filter_failure_modes(candidates, query)
    failure_modes = [c for c in filtered if c.get('type') == 'failure_mode']
    failure_mode_ids = [c['id'] for c in failure_modes]
    
    print(f"Query: {query}")
    print(f"  Canonical tokens: {canonical_tokens}")
    print(f"  Failure modes after filtering: {failure_mode_ids}")
    
    assert 'panic' in failure_mode_ids, f"Should include 'panic' (matches panic:), got {failure_mode_ids}"
    assert 'crash' not in failure_mode_ids, f"Should NOT include 'crash', got {failure_mode_ids}"
    
    print("  ✓ Test passed: panic: pattern matched")
    return True


def test_fatal_error_crash():
    """
    Test: "kubelet fatal error concurrent map writes"
    
    Expected:
    - anchors must include failure_mode "crash" (fatal error is a crash indicator)
    - anchors must NOT include failure_mode "panic"
    """
    query = "kubelet fatal error concurrent map writes"
    
    canonical_tokens = extract_canonical_tokens(query)
    
    candidates = [
        {'id': 'kubelet', 'type': 'component', 'final_score': 20},
        {'id': 'crash', 'type': 'failure_mode', 'final_score': 15},
        {'id': 'panic', 'type': 'failure_mode', 'final_score': 14},
    ]
    
    filtered = filter_failure_modes(candidates, query)
    failure_modes = [c for c in filtered if c.get('type') == 'failure_mode']
    failure_mode_ids = [c['id'] for c in failure_modes]
    
    print(f"Query: {query}")
    print(f"  Canonical tokens: {canonical_tokens}")
    print(f"  Failure modes after filtering: {failure_mode_ids}")
    
    assert 'crash' in failure_mode_ids, f"Should include 'crash' (fatal error), got {failure_mode_ids}"
    assert 'panic' not in failure_mode_ids, f"Should NOT include 'panic', got {failure_mode_ids}"
    
    print("  ✓ Test passed: fatal error maps to crash")
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("Failure Mode Precision Regression Tests")
    print("=" * 70)
    
    try:
        test_kubelet_crash_query()
        print()
        test_kube_scheduler_panic_query()
        print()
        test_panic_with_colon()
        print()
        test_fatal_error_crash()
        
        print("\n" + "=" * 70)
        print("All regression tests passed!")
        print("=" * 70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

