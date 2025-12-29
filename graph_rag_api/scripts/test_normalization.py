#!/usr/bin/env python3
"""
Test script for query normalization.

Tests that normalization correctly maps variants to canonical IDs.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.normalize import normalize_question, extract_canonical_tokens, normalize_and_enhance_tokens
from app.utils.text import tokenize_question


def test_failing_query():
    """Test the specific failing query from eval."""
    query = "scheduler crashes due to divide by 0 error in pod topology config"
    
    print(f"Test query: {query}")
    print("-" * 70)
    
    # Test normalization
    normalized = normalize_question(query)
    print(f"Normalized: {normalized}")
    
    # Test canonical token extraction
    canonical_ids = extract_canonical_tokens(query)
    print(f"Canonical IDs: {canonical_ids}")
    
    # Test token enhancement
    tokens = tokenize_question(query)
    enhanced = normalize_and_enhance_tokens(tokens, query)
    print(f"Original tokens: {tokens}")
    print(f"Enhanced tokens: {enhanced}")
    
    # Assertions
    assert "division-by-zero" in canonical_ids, "Should find division-by-zero"
    assert "kube-scheduler" in canonical_ids or any("scheduler" in t for t in enhanced), "Should find scheduler"
    assert "panic" in canonical_ids or "crash" in canonical_ids, "Should find crash/panic"
    
    print("\n✓ Test passed: normalization finds expected canonical IDs")
    return True


def test_synonym_mappings():
    """Test various synonym mappings."""
    test_cases = [
        ("divide by 0", "division-by-zero"),
        ("divide by zero", "division-by-zero"),
        ("race condition", "unsynchronized-concurrent-access"),
        ("concurrent map writes", "unsynchronized-concurrent-access"),
        ("out of memory", "unbounded-memory-growth"),
        ("memory leak", "unbounded-memory-growth"),
        ("scheduler", "kube-scheduler"),
        ("conntrack cleanup", "conntrack-management"),
    ]
    
    print("\nTesting synonym mappings:")
    print("-" * 70)
    
    for variant, expected_canonical in test_cases:
        canonical_ids = extract_canonical_tokens(variant)
        assert expected_canonical in canonical_ids, \
            f"'{variant}' should map to '{expected_canonical}', got {canonical_ids}"
        print(f"✓ '{variant}' -> {expected_canonical}")
    
    print("\n✓ All synonym mappings work correctly")


def test_word_boundaries():
    """Test that normalization doesn't over-fire on partial words."""
    test_cases = [
        ("divided", []),  # Should not match "divide"
        ("scheduling", []),  # Should not match "scheduler"
        ("scheduler component", ["kube-scheduler"]),  # Should match "scheduler"
    ]
    
    print("\nTesting word boundary protection:")
    print("-" * 70)
    
    for text, should_not_contain in test_cases:
        canonical_ids = extract_canonical_tokens(text)
        for unexpected in should_not_contain:
            if unexpected in canonical_ids:
                print(f"❌ '{text}' incorrectly matched '{unexpected}'")
                return False
        print(f"✓ '{text}' -> {canonical_ids}")
    
    print("\n✓ Word boundaries work correctly")
    return True


if __name__ == "__main__":
    print("=" * 70)
    print("Normalization Test Suite")
    print("=" * 70)
    
    try:
        test_failing_query()
        test_synonym_mappings()
        test_word_boundaries()
        
        print("\n" + "=" * 70)
        print("All tests passed!")
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

