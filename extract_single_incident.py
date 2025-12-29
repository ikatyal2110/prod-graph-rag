#!/usr/bin/env python3
import json

def extract_incident_128638():
    """
    Extract from incident #128638: kubelet crash - concurrent map writes
    
    Explicit facts:
    - kubelet component crashes
    - Error: "fatal error: concurrent map writes"
    - Location: ContainerMap.Add() method
    - Root cause: containerMap shared between three managers without synchronization
    - Multiple goroutines writing to same map concurrently
    - Classic race condition
    
    Normalized extraction:
    - Component: kubelet (node layer)
    - Failure mode: crash (panic -> crash)
    - Root cause: concurrency category (unsynchronized shared state access)
    - Concepts: concurrency-control, shared-state-management
    - Artifacts: containerMap (data_structure), ContainerMap.Add (function)
    """
    
    return {
        "components": [
            {"name": "kubelet", "layer": "node"}
        ],
        "concepts": [
            {"name": "concurrency-control", "domain": "runtime"},
            {"name": "shared-state-management", "domain": "runtime"}
        ],
        "incidents": [
            {"incident_id": "128638", "version": "", "severity": "high"}
        ],
        "failure_modes": [
            {"type": "crash"}
        ],
        "root_causes": [
            {"name": "unsynchronized-concurrent-access", "category": "concurrency"}
        ],
        "artifacts": [
            {"name": "containerMap", "kind": "data_structure"},
            {"name": "ContainerMap.Add", "kind": "function"}
        ],
        "edges": [
            {"from": "128638", "to": "kubelet", "type": "AFFECTS"},
            {"from": "128638", "to": "crash", "type": "EXHIBITS"},
            {"from": "128638", "to": "unsynchronized-concurrent-access", "type": "CAUSED_BY"},
            {"from": "unsynchronized-concurrent-access", "to": "crash", "type": "LEADS_TO"},
            {"from": "containerMap", "to": "unsynchronized-concurrent-access", "type": "INVOLVES"},
            {"from": "ContainerMap.Add", "to": "unsynchronized-concurrent-access", "type": "INVOLVES"},
            {"from": "kubelet", "to": "containerMap", "type": "USES"},
            {"from": "kubelet", "to": "ContainerMap.Add", "type": "USES"},
            {"from": "128638", "to": "concurrency-control", "type": "INVOLVES"},
            {"from": "128638", "to": "shared-state-management", "type": "INVOLVES"}
        ]
    }

# Output JSON
result = extract_incident_128638()
print(json.dumps(result, indent=2))
