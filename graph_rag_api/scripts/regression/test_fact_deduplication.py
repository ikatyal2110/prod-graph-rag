#!/usr/bin/env python3
"""
Regression test for fact deduplication.

Ensures that facts returned by /query contain no duplicate (from, rel, to) triples,
even when the database contains duplicate relationships (typed + :RELATIONSHIP).
"""

import sys
import os
import json
import requests
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def check_api_health(base_url: str) -> bool:
    """Check if API is reachable."""
    try:
        health_url = f"{base_url}/health"
        response = requests.get(health_url, timeout=5)
        response.raise_for_status()
        return True
    except Exception:
        return False

def query_api(question: str) -> dict:
    """Query the /query endpoint."""
    url = f"{API_BASE_URL}/query"
    payload = {"question": question}
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying API: {e}", file=sys.stderr)
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)

def test_no_duplicate_facts():
    """Test that facts contain no duplicate (from, rel, to) triples."""
    # Use a query that's likely to return multiple INVOLVES edges
    # Query about kubelet which should have multiple INVOLVES relationships
    query = "kubelet crash concurrent map writes"
    print(f"\nTesting query: '{query}'")
    response = query_api(query)
    
    facts = response.get('facts', [])
    print(f"  Total facts returned: {len(facts)}")
    
    # Check for duplicates
    fact_tuples = set()
    duplicates = []
    for fact in facts:
        fact_tuple = (fact.get('from'), fact.get('rel'), fact.get('to'))
        if fact_tuple in fact_tuples:
            duplicates.append(fact_tuple)
        else:
            fact_tuples.add(fact_tuple)
    
    if duplicates:
        print(f"  ❌ Found {len(duplicates)} duplicate facts:")
        for dup in duplicates[:10]:  # Show first 10
            print(f"    {dup}")
        if len(duplicates) > 10:
            print(f"    ... and {len(duplicates) - 10} more")
        return False
    else:
        print(f"  ✓ No duplicate facts found (all {len(facts)} facts are unique)")
        return True

def test_deterministic_ordering():
    """Test that facts are ordered deterministically."""
    query = "kubelet crash concurrent map writes"
    print(f"\nTesting deterministic ordering for query: '{query}'")
    
    # Run the same query multiple times and ensure facts are in the same order
    responses = []
    for i in range(3):
        response = query_api(query)
        facts = response.get('facts', [])
        responses.append(facts)
        time.sleep(0.1)  # Small delay between requests
    
    # Check that all responses have the same fact order
    first_facts = responses[0]
    for i, facts in enumerate(responses[1:], 1):
        if facts != first_facts:
            print(f"  ❌ Response {i+1} has different fact order than first response")
            print(f"    First response: {len(first_facts)} facts")
            print(f"    Response {i+1}: {len(facts)} facts")
            if len(facts) == len(first_facts):
                # Show first difference
                for j, (f1, f2) in enumerate(zip(first_facts, facts)):
                    if f1 != f2:
                        print(f"    First difference at index {j}:")
                        print(f"      First:  {f1}")
                        print(f"      Second: {f2}")
                        break
            return False
    
    print(f"  ✓ All {len(responses)} responses returned facts in identical order")
    return True

def test_involves_edges():
    """Test query that should return multiple INVOLVES edges."""
    # Query about a component that should have multiple INVOLVES relationships
    query = "kubelet issues"
    print(f"\nTesting query with multiple INVOLVES edges: '{query}'")
    response = query_api(query)
    
    facts = response.get('facts', [])
    involves_facts = [f for f in facts if f.get('rel') == 'INVOLVES']
    print(f"  Total facts: {len(facts)}")
    print(f"  INVOLVES facts: {len(involves_facts)}")
    
    # Check for duplicates in INVOLVES facts
    involves_tuples = set()
    duplicates = []
    for fact in involves_facts:
        fact_tuple = (fact.get('from'), fact.get('rel'), fact.get('to'))
        if fact_tuple in involves_tuples:
            duplicates.append(fact_tuple)
        else:
            involves_tuples.add(fact_tuple)
    
    if duplicates:
        print(f"  ❌ Found {len(duplicates)} duplicate INVOLVES facts:")
        for dup in duplicates:
            print(f"    {dup}")
        return False
    else:
        print(f"  ✓ No duplicate INVOLVES facts found")
        return True

if __name__ == "__main__":
    print("=" * 70)
    print("Regression Test: Fact Deduplication")
    print("=" * 70)

    # Wait for API to be ready
    print(f"Waiting for API at {API_BASE_URL} to be ready...")
    for i in range(10):
        if check_api_health(API_BASE_URL):
            print("API is ready!")
            break
        print(f"Attempt {i+1}/10: API not ready, waiting 3 seconds...")
        time.sleep(3)
    else:
        print("API did not become ready. Exiting.", file=sys.stderr)
        sys.exit(1)

    try:
        test1_passed = test_no_duplicate_facts()
        test2_passed = test_deterministic_ordering()
        test3_passed = test_involves_edges()
        
        print("\n" + "=" * 70)
        if test1_passed and test2_passed and test3_passed:
            print("All fact deduplication tests passed!")
            print("=" * 70)
            sys.exit(0)
        else:
            print("❌ Some tests failed:")
            if not test1_passed:
                print("  - No duplicate facts test failed")
            if not test2_passed:
                print("  - Deterministic ordering test failed")
            if not test3_passed:
                print("  - INVOLVES edges test failed")
            print("=" * 70)
            sys.exit(1)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

