#!/usr/bin/env python3
import json
from typing import Dict, List

def extract_architecture_cluster_architecture() -> Dict:
    """Extract from cluster-architecture.md"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "etcd", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "kube-scheduler", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "kube-controller-manager", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "cloud-controller-manager", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "kube-proxy", "type": "component", "attributes": {"layer": "networking"}},
            {"id": "control-plane", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "high-availability", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "fault-tolerance", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "node-management", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "global-cluster-decisions", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "control-plane", "to": "kube-apiserver", "type": "INVOLVES"},
            {"from": "control-plane", "to": "etcd", "type": "INVOLVES"},
            {"from": "control-plane", "to": "kube-scheduler", "type": "INVOLVES"},
            {"from": "control-plane", "to": "kube-controller-manager", "type": "INVOLVES"},
            {"from": "high-availability", "to": "control-plane", "type": "INVOLVES"},
            {"from": "fault-tolerance", "to": "control-plane", "type": "INVOLVES"},
            {"from": "kube-controller-manager", "to": "node-management", "type": "INVOLVES"},
            {"from": "kube-scheduler", "to": "global-cluster-decisions", "type": "INVOLVES"}
        ]
    }

def extract_architecture_kube_scheduler() -> Dict:
    """Extract from kube-scheduler.md"""
    return {
        "entities": [
            {"id": "kube-scheduler", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "pod-scheduling", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "node-selection", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "filtering", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "scoring", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "binding", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "feasible-nodes", "type": "concept", "attributes": {"domain": "scheduling"}}
        ],
        "edges": [
            {"from": "kube-scheduler", "to": "pod-scheduling", "type": "INVOLVES"},
            {"from": "pod-scheduling", "to": "node-selection", "type": "INVOLVES"},
            {"from": "node-selection", "to": "filtering", "type": "INVOLVES"},
            {"from": "node-selection", "to": "scoring", "type": "INVOLVES"},
            {"from": "scoring", "to": "binding", "type": "LEADS_TO"},
            {"from": "filtering", "to": "feasible-nodes", "type": "LEADS_TO"},
            {"from": "binding", "to": "kubelet", "type": "INVOLVES"}
        ]
    }

def extract_architecture_nodes() -> Dict:
    """Extract from nodes.md"""
    return {
        "entities": [
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "kube-proxy", "type": "component", "attributes": {"layer": "networking"}},
            {"id": "container-runtime", "type": "component", "attributes": {"layer": "node"}},
            {"id": "node-registration", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "node-health-checking", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "pod-execution", "type": "concept", "attributes": {"domain": "runtime"}}
        ],
        "edges": [
            {"from": "kubelet", "to": "node-registration", "type": "INVOLVES"},
            {"from": "kubelet", "to": "kube-apiserver", "type": "USES"},
            {"from": "kube-apiserver", "to": "node-health-checking", "type": "INVOLVES"},
            {"from": "kubelet", "to": "pod-execution", "type": "INVOLVES"},
            {"from": "container-runtime", "to": "pod-execution", "type": "INVOLVES"}
        ]
    }

def extract_architecture_controller() -> Dict:
    """Extract from controller.md"""
    return {
        "entities": [
            {"id": "kube-controller-manager", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "control-loop", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "desired-state", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "current-state", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "state-reconciliation", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "kube-controller-manager", "to": "control-loop", "type": "INVOLVES"},
            {"from": "control-loop", "to": "desired-state", "type": "INVOLVES"},
            {"from": "control-loop", "to": "current-state", "type": "INVOLVES"},
            {"from": "control-loop", "to": "state-reconciliation", "type": "INVOLVES"},
            {"from": "kube-controller-manager", "to": "kube-apiserver", "type": "USES"}
        ]
    }

def extract_architecture_etcd_operations() -> Dict:
    """Extract from etcd-operations.md"""
    return {
        "entities": [
            {"id": "etcd", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "etcd-cluster", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "leader-election", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "heartbeat", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "cluster-stability", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "resource-starvation", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "etcd", "to": "etcd-cluster", "type": "INVOLVES"},
            {"from": "etcd-cluster", "to": "leader-election", "type": "INVOLVES"},
            {"from": "leader-election", "to": "heartbeat", "type": "INVOLVES"},
            {"from": "heartbeat", "to": "cluster-stability", "type": "LEADS_TO"},
            {"from": "resource-starvation", "to": "cluster-stability", "type": "AFFECTS"}
        ]
    }

def extract_kep_624_scheduling_framework() -> Dict:
    """Extract from kep-624-scheduling-framework.md"""
    return {
        "entities": [
            {"id": "kube-scheduler", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "scheduling-framework", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "plugin-architecture", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "scheduling-plugins", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "extension-points", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "scheduling-cycle", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "binding-cycle", "type": "concept", "attributes": {"domain": "scheduling"}}
        ],
        "edges": [
            {"from": "kube-scheduler", "to": "scheduling-framework", "type": "USES"},
            {"from": "scheduling-framework", "to": "plugin-architecture", "type": "INVOLVES"},
            {"from": "scheduling-framework", "to": "scheduling-plugins", "type": "INVOLVES"},
            {"from": "scheduling-plugins", "to": "extension-points", "type": "INVOLVES"},
            {"from": "scheduling-cycle", "to": "binding-cycle", "type": "LEADS_TO"}
        ]
    }

def extract_kep_1040_priority_fairness() -> Dict:
    """Extract from kep-1040-priority-and-fairness.md"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "request-prioritization", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "fair-queuing", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "api-request-categorization", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "resource-limits", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "request-throttling", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "kube-apiserver", "to": "request-prioritization", "type": "INVOLVES"},
            {"from": "kube-apiserver", "to": "fair-queuing", "type": "INVOLVES"},
            {"from": "request-prioritization", "to": "api-request-categorization", "type": "INVOLVES"},
            {"from": "fair-queuing", "to": "resource-limits", "type": "INVOLVES"},
            {"from": "resource-limits", "to": "request-throttling", "type": "LEADS_TO"}
        ]
    }

def extract_kep_1281_network_proxy() -> Dict:
    """Extract from kep-1281-network-proxy.md"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "etcd", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "network-proxy", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "egress-traffic-control", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "control-plane-network-isolation", "type": "concept", "attributes": {"domain": "networking"}}
        ],
        "edges": [
            {"from": "kube-apiserver", "to": "network-proxy", "type": "USES"},
            {"from": "etcd", "to": "network-proxy", "type": "USES"},
            {"from": "network-proxy", "to": "egress-traffic-control", "type": "INVOLVES"},
            {"from": "egress-traffic-control", "to": "control-plane-network-isolation", "type": "LEADS_TO"}
        ]
    }

def extract_kep_2339_storageversion_api() -> Dict:
    """Extract from kep-2339-storageversion-api.md"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "etcd", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "storage-version-management", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "api-version-migration", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "ha-api-server-support", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "kube-apiserver", "to": "storage-version-management", "type": "INVOLVES"},
            {"from": "storage-version-management", "to": "etcd", "type": "USES"},
            {"from": "storage-version-management", "to": "api-version-migration", "type": "INVOLVES"},
            {"from": "storage-version-management", "to": "ha-api-server-support", "type": "INVOLVES"}
        ]
    }

def extract_kep_4743_kubernetes_etcd_interface() -> Dict:
    """Extract from kep-4743-kubernetes-etcd-interface.md"""
    return {
        "entities": [
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "etcd", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "etcd-client-interface", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "dependency-management", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "kube-apiserver", "to": "etcd", "type": "DEPENDS_ON"},
            {"from": "kube-apiserver", "to": "etcd-client-interface", "type": "USES"},
            {"from": "etcd-client-interface", "to": "dependency-management", "type": "INVOLVES"}
        ]
    }

def extract_kep_281_dynamic_kubelet_configuration() -> Dict:
    """Extract from kep-281-dynamic-kubelet-configuration.md"""
    return {
        "entities": [
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "kube-apiserver", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "dynamic-configuration", "type": "concept", "attributes": {"domain": "architecture"}},
            {"id": "configuration-management", "type": "concept", "attributes": {"domain": "architecture"}}
        ],
        "edges": [
            {"from": "kubelet", "to": "dynamic-configuration", "type": "INVOLVES"},
            {"from": "kubelet", "to": "kube-apiserver", "type": "USES"},
            {"from": "dynamic-configuration", "to": "configuration-management", "type": "INVOLVES"}
        ]
    }

def extract_kep_2862_fine_grained_kubelet_authz() -> Dict:
    """Extract from kep-2862-fine-grained-kubelet-authz.md"""
    return {
        "entities": [
            {"id": "kubelet", "type": "component", "attributes": {"layer": "node"}},
            {"id": "kubelet-api-authorization", "type": "concept", "attributes": {"domain": "security"}},
            {"id": "access-control", "type": "concept", "attributes": {"domain": "security"}}
        ],
        "edges": [
            {"from": "kubelet", "to": "kubelet-api-authorization", "type": "INVOLVES"},
            {"from": "kubelet-api-authorization", "to": "access-control", "type": "INVOLVES"}
        ]
    }

def extract_kep_265_ipvs_load_balancing() -> Dict:
    """Extract from kep-265-ipvs-load-balancing.md"""
    return {
        "entities": [
            {"id": "kube-proxy", "type": "component", "attributes": {"layer": "networking"}},
            {"id": "ipvs-load-balancing", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "load-balancing", "type": "concept", "attributes": {"domain": "networking"}}
        ],
        "edges": [
            {"from": "kube-proxy", "to": "ipvs-load-balancing", "type": "USES"},
            {"from": "ipvs-load-balancing", "to": "load-balancing", "type": "INVOLVES"}
        ]
    }

def extract_kep_752_endpointslices() -> Dict:
    """Extract from kep-752-endpointslices.md"""
    return {
        "entities": [
            {"id": "endpointslice", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "service-discovery", "type": "concept", "attributes": {"domain": "networking"}},
            {"id": "endpoint-scaling", "type": "concept", "attributes": {"domain": "networking"}}
        ],
        "edges": [
            {"from": "endpointslice", "to": "service-discovery", "type": "INVOLVES"},
            {"from": "endpointslice", "to": "endpoint-scaling", "type": "INVOLVES"}
        ]
    }

def extract_kep_1610_container_resource_autoscaling() -> Dict:
    """Extract from kep-1610-container-resource-autoscaling.md"""
    return {
        "entities": [
            {"id": "horizontal-pod-autoscaler", "type": "component", "attributes": {"layer": "control-plane"}},
            {"id": "container-resource-autoscaling", "type": "concept", "attributes": {"domain": "scheduling"}},
            {"id": "resource-scaling", "type": "concept", "attributes": {"domain": "scheduling"}}
        ],
        "edges": [
            {"from": "horizontal-pod-autoscaler", "to": "container-resource-autoscaling", "type": "INVOLVES"},
            {"from": "container-resource-autoscaling", "to": "resource-scaling", "type": "INVOLVES"}
        ]
    }

def merge_entities_and_edges(extractions: List[Dict]) -> Dict:
    """Merge all extractions, deduplicating entities by id"""
    all_entities = {}
    all_edges = []
    
    for ext in extractions:
        for entity in ext.get("entities", []):
            entity_id = entity["id"]
            if entity_id not in all_entities:
                all_entities[entity_id] = entity
        
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
        extract_architecture_cluster_architecture(),
        extract_architecture_kube_scheduler(),
        extract_architecture_nodes(),
        extract_architecture_controller(),
        extract_architecture_etcd_operations(),
        extract_kep_624_scheduling_framework(),
        extract_kep_1040_priority_fairness(),
        extract_kep_1281_network_proxy(),
        extract_kep_2339_storageversion_api(),
        extract_kep_4743_kubernetes_etcd_interface(),
        extract_kep_281_dynamic_kubelet_configuration(),
        extract_kep_2862_fine_grained_kubelet_authz(),
        extract_kep_265_ipvs_load_balancing(),
        extract_kep_752_endpointslices(),
        extract_kep_1610_container_resource_autoscaling()
    ]
    
    result = merge_entities_and_edges(extractions)
    
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()


