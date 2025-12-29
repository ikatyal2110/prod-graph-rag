#!/usr/bin/env python3
"""
Regression test for 135333 vs 128709 disambiguation.

Tests that queries correctly distinguish between:
- 135333: service name validation after IP allocation (validation-gaps, resource-creation-order)
- 128709: feature gate validation error (validation-error, feature-gate-compatibility)
"""

import sys
import os
import requests
import json

# Add parent directory (graph_rag_api) to path
script_dir = os.path.dirname(os.path.abspath(__file__))
graph_rag_api_dir = os.path.dirname(os.path.dirname(script_dir))
sys.path.insert(0, graph_rag_api_dir)

from app.utils.normalize import extract_canonical_tokens


def test_135333_query():
    """
    Test: "api server creates invalid IP address objects when service name is empty"
    
    Expected:
    - evidence.incident_ids[0] == "135333"
    - Should NOT return 128709
    """
    query = "api server creates invalid IP address objects when service name is empty"
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print(f"Testing 135333 query: {query}")
    print(f"API URL: {base_url}")
    
    # Check normalization
    canonical_tokens = extract_canonical_tokens(query)
    print(f"  Canonical tokens: {canonical_tokens}")
    
    # Expected tokens for 135333
    expected_tokens = {'validation-gaps', 'resource-creation-order', 'api-request-processing'}
    found_expected = expected_tokens.intersection(canonical_tokens)
    print(f"  Found 135333 tokens: {found_expected}")
    
    # Should NOT have 128709 tokens
    unexpected_tokens = {'validation-error', 'feature-gate-compatibility', 'podlogsquerysplitsstreams-feature-gate'}
    found_unexpected = unexpected_tokens.intersection(canonical_tokens)
    if found_unexpected:
        print(f"  ⚠ Warning: Found 128709 tokens: {found_unexpected}")
    
    # Query API
    try:
        response = requests.post(
            f"{base_url}/query",
            json={"question": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        incident_ids = data.get("evidence", {}).get("incident_ids", [])
        print(f"  API returned incident_ids: {incident_ids}")
        
        if not incident_ids:
            print("  ❌ No incident IDs returned")
            return False
        
        if incident_ids[0] != "135333":
            print(f"  ❌ Expected first incident_id to be '135333', got '{incident_ids[0]}'")
            return False
        
        if "128709" in incident_ids:
            print(f"  ❌ Should NOT include 128709, but it was in the results")
            return False
        
        print("  ✓ Test passed: 135333 returned correctly")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API request failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_128709_query():
    """
    Test: "validation error when accessing pod logs without stream parameter with PodLogsQuerySplitStreams feature gate"
    
    Expected:
    - evidence.incident_ids[0] == "128709"
    - Should include feature-gate related tokens
    """
    query = "validation error when accessing pod logs without stream parameter with PodLogsQuerySplitStreams feature gate"
    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    print(f"\nTesting 128709 query: {query}")
    print(f"API URL: {base_url}")
    
    # Check normalization
    canonical_tokens = extract_canonical_tokens(query)
    print(f"  Canonical tokens: {canonical_tokens}")
    
    # Expected tokens for 128709
    expected_tokens = {'validation-error', 'feature-gate-compatibility', 'podlogsquerysplitsstreams-feature-gate'}
    found_expected = expected_tokens.intersection(canonical_tokens)
    print(f"  Found 128709 tokens: {found_expected}")
    
    # Should NOT have 135333 tokens (unless also present, which is OK)
    unexpected_tokens = {'validation-gaps', 'resource-creation-order'}
    found_unexpected = unexpected_tokens.intersection(canonical_tokens)
    if found_unexpected:
        print(f"  ⚠ Note: Also found 135333 tokens: {found_unexpected} (may be OK)")
    
    # Query API
    try:
        response = requests.post(
            f"{base_url}/query",
            json={"question": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        incident_ids = data.get("evidence", {}).get("incident_ids", [])
        print(f"  API returned incident_ids: {incident_ids}")
        
        if not incident_ids:
            print("  ❌ No incident IDs returned")
            return False
        
        if incident_ids[0] != "128709":
            print(f"  ❌ Expected first incident_id to be '128709', got '{incident_ids[0]}'")
            return False
        
        print("  ✓ Test passed: 128709 returned correctly")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"  ❌ API request failed: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 70)
    print("135333 vs 128709 Disambiguation Regression Test")
    print("=" * 70)
    
    try:
        test1_passed = test_135333_query()
        test2_passed = test_128709_query()
        
        print("\n" + "=" * 70)
        if test1_passed and test2_passed:
            print("All regression tests passed!")
            sys.exit(0)
        else:
            print("Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

