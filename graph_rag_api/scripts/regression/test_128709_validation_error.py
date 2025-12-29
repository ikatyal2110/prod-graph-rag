#!/usr/bin/env python3
"""
Regression test for incident 128709 validation-error vs validation-gaps disambiguation.

Tests that query "kube-apiserver validation error feature gate podlogsquerysplitsstreams"
correctly anchors to validation-error (not validation-gaps) to match incident 128709.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.normalize import normalize_and_enhance_tokens, extract_canonical_tokens
from app.utils.text import tokenize_question


def test_validation_error_anchoring():
    """
    Test that "validation error" maps to validation-error, not validation-gaps.
    
    Query: "kube-apiserver validation error feature gate podlogsquerysplitsstreams"
    Expected:
    - anchors include root_cause: validation-error
    - anchors must NOT include root_cause: validation-gaps
    - This should help match incident 128709 (not 135333)
    """
    query = "kube-apiserver validation error feature gate podlogsquerysplitsstreams"
    
    print("=" * 70)
    print("Regression Test: Validation-Error vs Validation-Gaps Disambiguation")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    # Test normalization
    tokens = tokenize_question(query)
    enhanced = normalize_and_enhance_tokens(tokens, query)
    canonical_ids = extract_canonical_tokens(query)
    
    print(f"\nEnhanced tokens: {enhanced}")
    print(f"Canonical IDs: {canonical_ids}")
    
    # Check for validation-related root causes
    validation_rcs = [cid for cid in canonical_ids if 'validation' in cid and ('error' in cid or 'gaps' in cid)]
    print(f"\nValidation root causes found: {validation_rcs}")
    
    # Assertions
    assert 'validation-error' in canonical_ids, \
        f"Expected validation-error in canonical_ids, got {canonical_ids}"
    
    assert 'validation-gaps' not in canonical_ids, \
        f"Expected validation-gaps NOT in canonical_ids, got {canonical_ids}"
    
    # Also check enhanced tokens
    validation_rcs_enhanced = [t for t in enhanced if 'validation-error' in t or 'validation-gaps' in t]
    print(f"Validation root causes in enhanced tokens: {validation_rcs_enhanced}")
    
    assert 'validation-error' in enhanced, \
        f"Expected validation-error in enhanced tokens, got {enhanced}"
    
    assert 'validation-gaps' not in enhanced, \
        f"Expected validation-gaps NOT in enhanced tokens, got {enhanced}"
    
    print("\n✓ Normalization correctly maps 'validation error' to validation-error")
    print("✓ validation-gaps is correctly excluded")
    print("\nThis should help anchor extraction select validation-error for incident 128709")
    
    print("\n" + "=" * 70)
    print("Test passed! Validation-error disambiguation working correctly")
    print("=" * 70)
    
    return True


def test_validation_gaps_anchoring():
    """
    Test that "validation gap" correctly maps to validation-gaps.
    """
    query = "kube-apiserver validation gap"
    
    print("\n" + "=" * 70)
    print("Test: Validation-Gaps Anchoring")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    canonical_ids = extract_canonical_tokens(query)
    print(f"Canonical IDs: {canonical_ids}")
    
    validation_rcs = [cid for cid in canonical_ids if 'validation' in cid and ('error' in cid or 'gaps' in cid)]
    print(f"Validation root causes found: {validation_rcs}")
    
    assert 'validation-gaps' in canonical_ids, \
        f"Expected validation-gaps in canonical_ids, got {canonical_ids}"
    
    print("\n✓ Validation gap correctly maps to validation-gaps")


def test_generic_validation():
    """
    Test that generic "validation" does NOT map to either root cause.
    """
    query = "kube-apiserver validation"
    
    print("\n" + "=" * 70)
    print("Test: Generic Validation (should NOT map)")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    canonical_ids = extract_canonical_tokens(query)
    print(f"Canonical IDs: {canonical_ids}")
    
    validation_rcs = [cid for cid in canonical_ids if 'validation' in cid and ('error' in cid or 'gaps' in cid)]
    print(f"Validation root causes found: {validation_rcs}")
    
    assert len(validation_rcs) == 0, \
        f"Expected no validation root causes for generic 'validation', got {validation_rcs}"
    
    print("\n✓ Generic 'validation' does NOT map to validation-error or validation-gaps")


if __name__ == "__main__":
    try:
        test_validation_error_anchoring()
        test_validation_gaps_anchoring()
        test_generic_validation()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

