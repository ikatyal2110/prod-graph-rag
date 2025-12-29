"""Test script for /ask endpoint answer formatter

This script tests the deterministic answer formatting logic
by calling the formatter with mocked incident data.

Expected outputs are included as comments.

Run from graph_rag_api directory:
    python3 -m scripts.test_ask_formatter
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ask import AskService
from app.models.api import ExplainResponse


def test_formatter_with_full_data():
    """Test formatter with incident containing root cause, trigger, and artifacts."""
    print("=" * 60)
    print("Test 1: Incident with root cause + trigger + artifacts")
    print("=" * 60)
    
    # Mock incident data
    incident = ExplainResponse(
        incident_id="128638",
        severity="high",
        affects=["kubelet"],
        failure_modes=["crash"],
        root_causes=["unsynchronized-concurrent-access"],
        triggers=["pod-configuration"],
        concepts=[],
        artifacts_direct=[],
        artifacts_derived=["containerMap", "ContainerMap.Add"],
        artifacts=["containerMap", "ContainerMap.Add"],
        facts=[]
    )
    
    # Create a minimal service instance (we only need the formatter method)
    # Since the formatter is a private method, we'll test it via reflection
    # or create a minimal mock client
    mock_client = None  # We don't actually need it for the formatter
    mock_retrieval = None
    mock_explain = None
    
    service = AskService(mock_client, mock_retrieval, mock_explain)
    answer = service._format_single_incident_answer(incident)
    
    print(f"\nInput: Incident {incident.incident_id}")
    print(f"  - Components: {incident.affects}")
    print(f"  - Failure modes: {incident.failure_modes}")
    print(f"  - Root causes: {incident.root_causes}")
    print(f"  - Triggers: {incident.triggers}")
    print(f"  - Artifacts: {incident.artifacts}")
    
    print(f"\nOutput:")
    print(answer)
    
    print(f"\nExpected format:")
    print("Most relevant incident: 128638.")
    print("Component: kubelet. Failure mode: crash.")
    print("Root cause: unsynchronized-concurrent-access.")
    print("Trigger: pod-configuration.")
    print("Artifacts: ContainerMap.Add, containerMap.")
    print("Evidence is grounded in graph relationships and linked nodes.")
    print()


def test_formatter_minimal_data():
    """Test formatter with incident containing only component + failure mode."""
    print("=" * 60)
    print("Test 2: Incident with only component + failure mode")
    print("=" * 60)
    
    # Mock incident data with minimal fields
    incident = ExplainResponse(
        incident_id="124930",
        severity="high",
        affects=["kube-scheduler"],
        failure_modes=["panic"],
        root_causes=[],  # No root cause
        triggers=[],  # No triggers
        concepts=[],
        artifacts_direct=[],
        artifacts_derived=[],
        artifacts=[],  # No artifacts
        facts=[]
    )
    
    mock_client = None
    mock_retrieval = None
    mock_explain = None
    
    service = AskService(mock_client, mock_retrieval, mock_explain)
    answer = service._format_single_incident_answer(incident)
    
    print(f"\nInput: Incident {incident.incident_id}")
    print(f"  - Components: {incident.affects}")
    print(f"  - Failure modes: {incident.failure_modes}")
    print(f"  - Root causes: {incident.root_causes}")
    print(f"  - Triggers: {incident.triggers}")
    print(f"  - Artifacts: {incident.artifacts}")
    
    print(f"\nOutput:")
    print(answer)
    
    print(f"\nExpected format:")
    print("Most relevant incident: 124930.")
    print("Component: kube-scheduler. Failure mode: panic.")
    print("Evidence is grounded in graph relationships and linked nodes.")
    print()
    
    # Verify root cause, trigger, and artifacts lines are omitted
    assert "Root cause" not in answer, "Root cause should be omitted when empty"
    assert "Trigger" not in answer, "Trigger should be omitted when empty"
    assert "Artifacts" not in answer, "Artifacts should be omitted when empty"
    print("✓ Verification passed: Conditional lines correctly omitted")


def test_formatter_multiple_values():
    """Test formatter with multiple components and failure modes."""
    print("=" * 60)
    print("Test 3: Multiple components and failure modes (sorted)")
    print("=" * 60)
    
    incident = ExplainResponse(
        incident_id="99999",
        severity="medium",
        affects=["kubelet", "kube-proxy", "kube-apiserver"],  # Multiple, should be sorted
        failure_modes=["crash", "degradation"],  # Multiple, should be sorted
        root_causes=["root-cause-1", "root-cause-2"],  # Multiple, should be sorted
        triggers=[],
        concepts=[],
        artifacts_direct=[],
        artifacts_derived=["artifact-z", "artifact-a"],  # Should be sorted
        artifacts=["artifact-z", "artifact-a"],
        facts=[]
    )
    
    mock_client = None
    mock_retrieval = None
    mock_explain = None
    
    service = AskService(mock_client, mock_retrieval, mock_explain)
    answer = service._format_single_incident_answer(incident)
    
    print(f"\nInput: Incident {incident.incident_id}")
    print(f"  - Components: {incident.affects}")
    print(f"  - Failure modes: {incident.failure_modes}")
    print(f"  - Root causes: {incident.root_causes}")
    print(f"  - Artifacts: {incident.artifacts}")
    
    print(f"\nOutput:")
    print(answer)
    
    print(f"\nExpected: All lists should be sorted lexicographically")
    print("  - Components: kube-apiserver, kube-proxy, kubelet")
    print("  - Failure modes: crash, degradation")
    print("  - Root causes: root-cause-1, root-cause-2")
    print("  - Artifacts: artifact-a, artifact-z")
    print()
    
    # Verify sorting
    assert "kube-apiserver, kube-proxy, kubelet" in answer or "kube-apiserver,kube-proxy,kubelet" in answer
    assert "artifact-a, artifact-z" in answer or "artifact-a,artifact-z" in answer
    print("✓ Verification passed: Lists are sorted correctly")


if __name__ == "__main__":
    print("\nTesting /ask endpoint answer formatter")
    print("=" * 60)
    print()
    
    try:
        test_formatter_with_full_data()
        test_formatter_minimal_data()
        test_formatter_multiple_values()
        
        print("=" * 60)
        print("All tests completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError during testing: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

