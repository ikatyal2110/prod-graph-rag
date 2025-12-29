#!/usr/bin/env python3
"""
Regression test for incident 128709 anchor extraction.

Tests that query "kube-apiserver validation error feature gate podlogsquerysplitsstreams"
returns appropriate anchors including feature gate trigger/concept to match incident 128709.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.normalize import normalize_and_enhance_tokens
from app.utils.text import tokenize_question


def test_anchor_extraction_128709():
    """
    Test that anchor extraction includes feature gate trigger/concept for incident 128709.
    
    Expected anchors should include:
    - component: kube-apiserver
    - trigger: podlogsquerysplitsstreams-feature-gate (or similar)
    - concept: feature-gate-compatibility or api-backward-compatibility
    """
    query = "kube-apiserver validation error feature gate podlogsquerysplitsstreams"
    
    print("=" * 70)
    print("Regression Test: Incident 128709 Anchor Extraction")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    # Test normalization
    tokens = tokenize_question(query)
    enhanced = normalize_and_enhance_tokens(tokens, query)
    
    print(f"\nEnhanced tokens: {enhanced}")
    
    # Check for expected canonical IDs
    expected_anchors = [
        'kube-apiserver',
        'podlogsquerysplitsstreams-feature-gate',
        'feature-gate-compatibility',
        'api-backward-compatibility',
    ]
    
    found_anchors = [a for a in expected_anchors if a in enhanced]
    
    print(f"\nExpected anchor canonical IDs found: {found_anchors}")
    
    # Assertions
    assert 'kube-apiserver' in enhanced, \
        f"Expected kube-apiserver in enhanced tokens, got {enhanced}"
    
    # Must have at least one feature gate related term
    feature_gate_terms = [
        'podlogsquerysplitsstreams-feature-gate',
        'feature-gate-compatibility',
        'api-backward-compatibility',
    ]
    has_feature_gate = any(term in enhanced for term in feature_gate_terms)
    assert has_feature_gate, \
        f"Expected at least one feature gate term in {feature_gate_terms}, got {enhanced}"
    
    print("\n✓ Normalization test passed")
    print("✓ Expected canonical IDs are present")
    print("✓ Feature gate terms are found")
    
    print("\n" + "=" * 70)
    print("Test passed! Anchor extraction should now match incident 128709")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        test_anchor_extraction_128709()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

