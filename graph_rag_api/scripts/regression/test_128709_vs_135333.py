#!/usr/bin/env python3
"""
Regression test for incident 128709 vs 135333 disambiguation.

Tests that queries correctly distinguish between:
- 128709: feature gate + podlogsquerysplitsstreams + validation-error
- 135333: creation order + validation-gaps
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.normalize import normalize_and_enhance_tokens, extract_canonical_tokens
from app.utils.text import tokenize_question


def test_128709_query():
    """
    Test query for incident 128709:
    "kube-apiserver feature gate validation podlogsquerysplitsstreams error"
    
    Expected anchors:
    - trigger: podlogsquerysplitsstreams-feature-gate
    - root_cause: validation-error
    - component: kube-apiserver
    - concept: feature-gate-compatibility (optional)
    
    Should NOT anchor: validation-gaps
    """
    query = "kube-apiserver feature gate validation podlogsquerysplitsstreams error"
    
    print("=" * 70)
    print("Regression Test: Incident 128709 Query")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    # Test normalization
    tokens = tokenize_question(query)
    enhanced = normalize_and_enhance_tokens(tokens, query)
    canonical_ids = extract_canonical_tokens(query)
    
    print(f"\nEnhanced tokens: {enhanced}")
    print(f"Canonical IDs: {canonical_ids}")
    
    # Check for expected anchors
    has_podlogs_trigger = 'podlogsquerysplitsstreams-feature-gate' in canonical_ids
    has_validation_error = 'validation-error' in canonical_ids
    has_validation_gaps = 'validation-gaps' in canonical_ids
    has_kube_apiserver = 'kube-apiserver' in canonical_ids
    
    print(f"\nAnchor checks:")
    print(f"  ✓ podlogsquerysplitsstreams-feature-gate: {has_podlogs_trigger}")
    print(f"  ✓ validation-error: {has_validation_error}")
    print(f"  ✗ validation-gaps (should NOT be present): {has_validation_gaps}")
    print(f"  ✓ kube-apiserver: {has_kube_apiserver}")
    
    # Assertions
    assert has_podlogs_trigger, \
        f"Expected podlogsquerysplitsstreams-feature-gate in canonical_ids, got {canonical_ids}"
    
    assert has_validation_error, \
        f"Expected validation-error in canonical_ids, got {canonical_ids}"
    
    assert not has_validation_gaps, \
        f"Expected validation-gaps NOT in canonical_ids, got {canonical_ids}"
    
    assert has_kube_apiserver, \
        f"Expected kube-apiserver in canonical_ids, got {canonical_ids}"
    
    print("\n✓ All assertions passed for 128709 query")
    print("This query should match incident 128709")
    
    return True


def test_135333_query():
    """
    Test query for incident 135333:
    "service creation fails validation because name checked after IP allocation"
    
    Expected anchors:
    - concept: resource-creation-order (or api-request-processing)
    - root_cause: validation-gaps
    - component: kube-apiserver (if present)
    
    Should NOT anchor: validation-error, podlogsquerysplitsstreams-feature-gate
    """
    query = "service creation fails validation because name checked after IP allocation"
    
    print("\n" + "=" * 70)
    print("Regression Test: Incident 135333 Query")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    # Test normalization
    tokens = tokenize_question(query)
    enhanced = normalize_and_enhance_tokens(tokens, query)
    canonical_ids = extract_canonical_tokens(query)
    
    print(f"\nEnhanced tokens: {enhanced}")
    print(f"Canonical IDs: {canonical_ids}")
    
    # Check for expected anchors
    has_resource_creation_order = 'resource-creation-order' in canonical_ids
    has_validation_gaps = 'validation-gaps' in canonical_ids
    has_validation_error = 'validation-error' in canonical_ids
    has_podlogs_trigger = 'podlogsquerysplitsstreams-feature-gate' in canonical_ids
    
    print(f"\nAnchor checks:")
    print(f"  ✓ resource-creation-order: {has_resource_creation_order}")
    print(f"  ✓ validation-gaps: {has_validation_gaps}")
    print(f"  ✗ validation-error (should NOT be present): {has_validation_error}")
    print(f"  ✗ podlogsquerysplitsstreams-feature-gate (should NOT be present): {has_podlogs_trigger}")
    
    # Assertions
    assert has_resource_creation_order, \
        f"Expected resource-creation-order in canonical_ids, got {canonical_ids}"
    
    assert has_validation_gaps, \
        f"Expected validation-gaps in canonical_ids, got {canonical_ids}"
    
    assert not has_validation_error, \
        f"Expected validation-error NOT in canonical_ids, got {canonical_ids}"
    
    assert not has_podlogs_trigger, \
        f"Expected podlogsquerysplitsstreams-feature-gate NOT in canonical_ids, got {canonical_ids}"
    
    print("\n✓ All assertions passed for 135333 query")
    print("This query should match incident 135333")
    
    return True


if __name__ == "__main__":
    try:
        test_128709_query()
        test_135333_query()
        print("\n" + "=" * 70)
        print("All regression tests passed!")
        print("=" * 70)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

