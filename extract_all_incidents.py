#!/usr/bin/env python3
import json
from typing import Dict, List, Set

def extract_incident_128638() -> Dict:
    """Incident #128638: kubelet crash - concurrent map writes"""
    return {
        "entities": [
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "128638", "type": "incident", "attributes": {"severity": "high", "version": ""}},
            {"id": "crash", "type": "failure_mode", "attributes": {}},
            {"id": "unsynchronized-concurrent-access", "type": "root_cause", "attributes": {"category": "concurrency"}},
            {"id": "concurrency-control", "type": "concept", "attributes": {"domain": "runtime"}},
            {"id": "shared-state-management", "type": "concept", "attributes": {"domain": "runtime"}},
            {"id": "containerMap", "type": "artifact", "attributes": {"kind": "data_structure"}},
            {"id": "ContainerMap.Add", "type": "artifact", "attributes": {"kind": "function"}}
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

def extract_incident_124930() -> Dict:
    """Incident #124930: kube-scheduler panic - integer divide by zero"""
    return {
        "entities": [
            {"id": "kube-scheduler", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "124930", "type": "incident", "attributes": {"severity": "high", "version": "v1.30.0"}},
            {"id": "panic", "type": "failure_mode", "attributes": {}},
            {"id": "division-by-zero", "type": "root_cause", "attributes": {"category": "arithmetic"}},
            {"id": "scheduler-scoring-logic", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "edge-case-handling", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "pod-configuration", "type": "trigger", "attributes": {"trigger_type": "config"}}
        ],
        "edges": [
            {"from": "124930", "to": "kube-scheduler", "type": "AFFECTS"},
            {"from": "124930", "to": "panic", "type": "EXHIBITS"},
            {"from": "124930", "to": "division-by-zero", "type": "CAUSED_BY"},
            {"from": "124930", "to": "pod-configuration", "type": "TRIGGERED_BY"},
            {"from": "division-by-zero", "to": "panic", "type": "LEADS_TO"},
            {"from": "pod-configuration", "to": "division-by-zero", "type": "ACTIVATES"},
            {"from": "124930", "to": "scheduler-scoring-logic", "type": "INVOLVES"},
            {"from": "124930", "to": "edge-case-handling", "type": "INVOLVES"}
        ]
    }

def extract_incident_129982() -> Dict:
    """Incident #129982: kube-proxy OOM - excessive conntrack cleanup"""
    return {
        "entities": [
            {"id": "kube-proxy", "type": "component", "attributes": {"layer": "networking"}},
            {"id": "129982", "type": "incident", "attributes": {"severity": "critical", "version": "v1.32"}},
            {"id": "oom", "type": "failure_mode", "attributes": {}},
            {"id": "unbounded-memory-growth", "type": "root_cause", "attributes": {"category": "resource-management"}},
            {"id": "conntrack-management", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "resource-cleanup", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "udp-endpoint-change", "type": "trigger", "attributes": {"trigger_type": "network"}},
            {"id": "pod-with-udp-port-update", "type": "trigger", "attributes": {"trigger_type": "workload"}},
            {"id": "vishvananda/netlink", "type": "artifact", "attributes": {"kind": "library"}},
            {"id": "conntrack_linux.go", "type": "artifact", "attributes": {"kind": "file"}},
            {"id": "conntrack-table", "type": "artifact", "attributes": {"kind": "data_structure"}}
        ],
        "edges": [
            {"from": "129982", "to": "kube-proxy", "type": "AFFECTS"},
            {"from": "129982", "to": "oom", "type": "EXHIBITS"},
            {"from": "129982", "to": "unbounded-memory-growth", "type": "CAUSED_BY"},
            {"from": "129982", "to": "udp-endpoint-change", "type": "TRIGGERED_BY"},
            {"from": "129982", "to": "pod-with-udp-port-update", "type": "TRIGGERED_BY"},
            {"from": "unbounded-memory-growth", "to": "oom", "type": "LEADS_TO"},
            {"from": "udp-endpoint-change", "to": "unbounded-memory-growth", "type": "ACTIVATES"},
            {"from": "pod-with-udp-port-update", "to": "udp-endpoint-change", "type": "LEADS_TO"},
            {"from": "vishvananda/netlink", "to": "unbounded-memory-growth", "type": "INVOLVES"},
            {"from": "conntrack_linux.go", "to": "unbounded-memory-growth", "type": "INVOLVES"},
            {"from": "conntrack-table", "to": "unbounded-memory-growth", "type": "INVOLVES"},
            {"from": "129982", "to": "conntrack-management", "type": "INVOLVES"},
            {"from": "129982", "to": "resource-cleanup", "type": "INVOLVES"}
        ]
    }

def extract_incident_135333() -> Dict:
    """Incident #135333: kube-apiserver - invalid IPAddress creation"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "135333", "type": "incident", "attributes": {"severity": "medium", "version": ""}},
            {"id": "validation-gaps", "type": "root_cause", "attributes": {"category": "validation"}},
            {"id": "api-request-processing", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "resource-creation-order", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "ipallocator.go", "type": "artifact", "attributes": {"kind": "file"}},
            {"id": "serviceToRef", "type": "artifact", "attributes": {"kind": "function"}},
            {"id": "IPAddress", "type": "artifact", "attributes": {"kind": "data_structure"}}
        ],
        "edges": [
            {"from": "135333", "to": "kube-apiserver", "type": "AFFECTS"},
            {"from": "135333", "to": "validation-gaps", "type": "CAUSED_BY"},
            {"from": "ipallocator.go", "to": "validation-gaps", "type": "INVOLVES"},
            {"from": "serviceToRef", "to": "validation-gaps", "type": "INVOLVES"},
            {"from": "IPAddress", "to": "validation-gaps", "type": "INVOLVES"},
            {"from": "kube-apiserver", "to": "ipallocator.go", "type": "USES"},
            {"from": "kube-apiserver", "to": "serviceToRef", "type": "USES"},
            {"from": "135333", "to": "api-request-processing", "type": "INVOLVES"},
            {"from": "135333", "to": "resource-creation-order", "type": "INVOLVES"}
        ]
    }

def extract_incident_128709() -> Dict:
    """Incident #128709: kube-apiserver - PodLogsQuerySplitStreams validation error"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "128709", "type": "incident", "attributes": {"severity": "medium", "version": ""}},
            {"id": "validation-error", "type": "root_cause", "attributes": {"category": "validation"}},
            {"id": "feature-gate-compatibility", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "api-backward-compatibility", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "podlogsquerysplitsstreams-feature-gate", "type": "trigger", "attributes": {"trigger_type": "config"}}
        ],
        "edges": [
            {"from": "128709", "to": "kube-apiserver", "type": "AFFECTS"},
            {"from": "128709", "to": "validation-error", "type": "CAUSED_BY"},
            {"from": "128709", "to": "podlogsquerysplitsstreams-feature-gate", "type": "TRIGGERED_BY"},
            {"from": "podlogsquerysplitsstreams-feature-gate", "to": "validation-error", "type": "ACTIVATES"},
            {"from": "128709", "to": "feature-gate-compatibility", "type": "INVOLVES"},
            {"from": "128709", "to": "api-backward-compatibility", "type": "INVOLVES"}
        ]
    }

def extract_incident_78308() -> Dict:
    """Incident #78308: CVE-2019-11245 - container uid changes to root"""
    return {
        "entities": [
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "78308", "type": "incident", "attributes": {"severity": "medium", "version": "v1.13.6"}},
            {"id": "degradation", "type": "failure_mode", "attributes": {}},
            {"id": "incorrect-lifecycle-state-handling", "type": "root_cause", "attributes": {"category": "lifecycle"}},
            {"id": "container-security", "type": "concept", "attributes": {"domain": "security"}},
            {"id": "container-lifecycle-management", "type": "concept", "attributes": {"domain": "runtime"}},
            {"id": "container-restart", "type": "trigger", "attributes": {"trigger_type": "runtime"}},
            {"id": "pre-pulled-image", "type": "trigger", "attributes": {"trigger_type": "runtime"}}
        ],
        "edges": [
            {"from": "78308", "to": "kubelet", "type": "AFFECTS"},
            {"from": "78308", "to": "degradation", "type": "EXHIBITS"},
            {"from": "78308", "to": "incorrect-lifecycle-state-handling", "type": "CAUSED_BY"},
            {"from": "78308", "to": "container-restart", "type": "TRIGGERED_BY"},
            {"from": "78308", "to": "pre-pulled-image", "type": "TRIGGERED_BY"},
            {"from": "incorrect-lifecycle-state-handling", "to": "degradation", "type": "LEADS_TO"},
            {"from": "container-restart", "to": "incorrect-lifecycle-state-handling", "type": "ACTIVATES"},
            {"from": "pre-pulled-image", "to": "incorrect-lifecycle-state-handling", "type": "ACTIVATES"},
            {"from": "78308", "to": "container-security", "type": "INVOLVES"},
            {"from": "78308", "to": "container-lifecycle-management", "type": "INVOLVES"}
        ]
    }

def merge_entities_and_edges(extractions: List[Dict]) -> Dict:
    """Merge all extractions, deduplicating entities by id"""
    all_entities = {}
    all_edges = []
    
    for ext in extractions:
        # Merge entities (deduplicate by id)
        for entity in ext.get("entities", []):
            entity_id = entity["id"]
            if entity_id not in all_entities:
                all_entities[entity_id] = entity
            else:
                # Merge attributes if same id but different types (shouldn't happen, but handle it)
                existing = all_entities[entity_id]
                if existing["type"] != entity["type"]:
                    # Keep the first one, log warning
                    pass
        
        # Collect all edges
        all_edges.extend(ext.get("edges", []))
    
    # Deduplicate edges
    seen_edges = set()
    unique_edges = []
    for edge in all_edges:
        edge_key = (edge["from"], edge["to"], edge["type"])
        if edge_key not in seen_edges:
            seen_edges.add(edge_key)
            unique_edges.append(edge)
    
    return {
        "entities": list(all_entities.values()),
        "edges": unique_edges
    }

def main():
    extractions = [
        extract_incident_128638(),
        extract_incident_124930(),
        extract_incident_129982(),
        extract_incident_135333(),
        extract_incident_128709(),
        extract_incident_78308()
    ]
    
    result = merge_entities_and_edges(extractions)
    
    # Output as JSON
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()


