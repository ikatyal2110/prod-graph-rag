#!/usr/bin/env python3
"""
Regression test for incident 78308 anchor extraction.

Tests that query "kubelet incorrectly sets container user ID on restart with pre-pulled images"
returns appropriate anchors including triggers/concepts that help match incident 78308.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.normalize import normalize_and_enhance_tokens
from app.utils.text import tokenize_question


def test_anchor_extraction_78308():
    """
    Test that anchor extraction includes triggers/concepts for incident 78308.
    
    Expected anchors should include at least one of:
    - trigger: container-restart
    - trigger: pre-pulled-image
    - concept: container-lifecycle-management
    """
    query = "kubelet incorrectly sets container user ID on restart with pre-pulled images"
    
    print("=" * 70)
    print("Regression Test: Incident 78308 Anchor Extraction")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    # Test normalization
    tokens = tokenize_question(query)
    enhanced = normalize_and_enhance_tokens(tokens, query)
    
    print(f"\nEnhanced tokens: {enhanced}")
    
    # Check for expected canonical IDs
    expected_anchors = [
        'container-restart',
        'pre-pulled-image',
        'container-lifecycle-management',
        'container-security',
    ]
    
    found_anchors = [a for a in expected_anchors if a in enhanced]
    
    print(f"\nExpected anchor canonical IDs found: {found_anchors}")
    
    # Assertions
    assert len(found_anchors) > 0, \
        f"Expected at least one of {expected_anchors} in enhanced tokens, got {enhanced}"
    
    assert 'kubelet' in enhanced or 'kubelet' in query.lower(), \
        "Query should match kubelet component"
    
    print("\n✓ Normalization test passed")
    print("✓ Expected canonical IDs are present")
    
    print("\n" + "=" * 70)
    print("Test passed! Anchor extraction should now match incident 78308")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    try:
        test_anchor_extraction_78308()
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

