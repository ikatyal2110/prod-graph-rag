"""Test script for key_facts deterministic ordering

This script tests that key_facts are sorted deterministically
according to the required ordering rules.

Run from graph_rag_api directory:
    PYTHONPATH=. python3 scripts/test_key_facts_order.py
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ask import AskService
from app.models.api import Fact


def test_key_facts_ordering():
    """Test that key_facts are sorted correctly with all rel types."""
    print("=" * 60)
    print("Test: Key Facts Deterministic Ordering")
    print("=" * 60)
    
    # Create shuffled list of facts with all relationship types
    # Include multiple INVOLVES entries to test secondary sorting
    facts = [
        Fact(from_id="incident1", rel="USES", to_id="artifact-z"),
        Fact(from_id="incident1", rel="AFFECTS", to_id="component-b"),
        Fact(from_id="incident1", rel="INVOLVES", to_id="concept-y"),
        Fact(from_id="incident1", rel="TRIGGERED_BY", to_id="trigger-a"),
        Fact(from_id="incident1", rel="EXHIBITS", to_id="failure-mode-z"),
        Fact(from_id="incident1", rel="CAUSED_BY", to_id="root-cause-a"),
        Fact(from_id="incident1", rel="INVOLVES", to_id="concept-a"),  # Second INVOLVES
        Fact(from_id="incident1", rel="AFFECTS", to_id="component-a"),  # Second AFFECTS
        Fact(from_id="incident2", rel="AFFECTS", to_id="component-a"),  # Same rel and to, different from
        Fact(from_id="incident1", rel="UNKNOWN_REL", to_id="target-z"),  # Unknown rel type
        Fact(from_id="incident1", rel="UNKNOWN_REL", to_id="target-a"),  # Unknown rel, sorted by to
    ]
    
    print(f"\nInput: {len(facts)} facts (shuffled order)")
    print("Relationship types in input:")
    for fact in facts:
        print(f"  - {fact.rel}: {fact.from_id} -> {fact.to_id}")
    
    # Create service instance (we only need the sorting method)
    service = AskService(None, None, None)
    sorted_facts = service._sort_key_facts(facts)
    
    print(f"\nOutput: {len(sorted_facts)} facts (after sorting and deduplication)")
    print("Relationship types in output (should be in required order):")
    for fact in sorted_facts:
        print(f"  - {fact.rel}: {fact.from_id} -> {fact.to_id}")
    
    # Expected order:
    # 1. AFFECTS (component-a from incident1, then component-a from incident2, then component-b)
    # 2. EXHIBITS (failure-mode-z)
    # 3. CAUSED_BY (root-cause-a)
    # 4. TRIGGERED_BY (trigger-a)
    # 5. INVOLVES (concept-a, then concept-y)
    # 6. USES (artifact-z)
    # 7. UNKNOWN_REL (target-a, then target-z)
    
    expected_order = [
        ("AFFECTS", "incident1", "component-a"),
        ("AFFECTS", "incident2", "component-a"),
        ("AFFECTS", "incident1", "component-b"),
        ("EXHIBITS", "incident1", "failure-mode-z"),
        ("CAUSED_BY", "incident1", "root-cause-a"),
        ("TRIGGERED_BY", "incident1", "trigger-a"),
        ("INVOLVES", "incident1", "concept-a"),
        ("INVOLVES", "incident1", "concept-y"),
        ("USES", "incident1", "artifact-z"),
        ("UNKNOWN_REL", "incident1", "target-a"),
        ("UNKNOWN_REL", "incident1", "target-z"),
    ]
    
    print(f"\nExpected order:")
    for rel, from_id, to_id in expected_order:
        print(f"  - {rel}: {from_id} -> {to_id}")
    
    # Verify ordering
    print(f"\nVerifying ordering...")
    assert len(sorted_facts) == len(expected_order), \
        f"Expected {len(expected_order)} facts, got {len(sorted_facts)}"
    
    for i, (fact, expected) in enumerate(zip(sorted_facts, expected_order)):
        expected_rel, expected_from, expected_to = expected
        assert fact.rel == expected_rel, \
            f"Position {i}: Expected rel '{expected_rel}', got '{fact.rel}'"
        assert fact.from_id == expected_from, \
            f"Position {i}: Expected from '{expected_from}', got '{fact.from_id}'"
        assert fact.to_id == expected_to, \
            f"Position {i}: Expected to '{expected_to}', got '{fact.to_id}'"
    
    print("✓ All facts in correct order")
    
    # Test deduplication: add a duplicate fact
    print(f"\nTesting deduplication...")
    facts_with_duplicate = facts + [
        Fact(from_id="incident1", rel="AFFECTS", to_id="component-a")  # Duplicate
    ]
    sorted_dedup = service._sort_key_facts(facts_with_duplicate)
    
    # Count occurrences of the duplicate fact
    duplicate_count = sum(
        1 for f in sorted_dedup
        if f.from_id == "incident1" and f.rel == "AFFECTS" and f.to_id == "component-a"
    )
    assert duplicate_count == 1, \
        f"Expected 1 occurrence after deduplication, got {duplicate_count}"
    
    print(f"✓ Deduplication works correctly (duplicate removed)")
    
    # Test that input is not mutated
    print(f"\nTesting that input is not mutated...")
    original_facts_list = list(facts)
    service._sort_key_facts(facts)
    assert facts == original_facts_list, "Input list was mutated!"
    print("✓ Input list not mutated")
    
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    try:
        exit_code = test_key_facts_ordering()
        sys.exit(exit_code)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

