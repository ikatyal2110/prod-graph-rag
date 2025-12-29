#!/usr/bin/env python3
"""
Regression test for artifact anchor filtering.

Tests that:
1. Non-code queries do NOT include artifact anchors
2. Code queries DO allow artifact anchors
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.code_detection import is_code_query


def test_non_code_query_no_artifacts():
    """
    Test that non-code queries are correctly identified.
    """
    query = "service creation fails validation because name checked after IP allocation"
    
    print("=" * 70)
    print("Test: Non-Code Query Detection")
    print("=" * 70)
    print(f"\nQuery: {query}")
    
    is_code = is_code_query(query)
    print(f"\nIs code query: {is_code}")
    
    assert not is_code, \
        f"Expected non-code query, but is_code_query returned True"
    
    print("\n✓ Non-code query correctly identified")
    print("✓ Artifact anchors should be filtered out for this query")


def test_code_query_allows_artifacts():
    """
    Test that code queries are correctly identified.
    """
    queries = [
        "containerMap panic at runtime",
        "ContainerMap.Add function crash",
        "serviceToRef.method fails",
        "stack trace in /path/to/file.go",
        "fatal error: nil pointer dereference",
    ]
    
    print("\n" + "=" * 70)
    print("Test: Code Query Detection")
    print("=" * 70)
    
    for query in queries:
        print(f"\nQuery: {query}")
        is_code = is_code_query(query)
        print(f"Is code query: {is_code}")
        
        assert is_code, \
            f"Expected code query, but is_code_query returned False for: {query}"
        
        print("✓ Code query correctly identified")
    
    print("\n✓ All code queries correctly identified")
    print("✓ Artifact anchors should be allowed for these queries")


if __name__ == "__main__":
    try:
        test_non_code_query_no_artifacts()
        test_code_query_allows_artifacts()
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

