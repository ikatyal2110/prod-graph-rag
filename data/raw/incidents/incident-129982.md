# Issue #129982: Excessive conntrack cleanup causes high memory (12GB) and CPU usage when any Pod with a UDP port changes

## Issue Title
Excessive conntrack cleanup causes high memory (12GB) and CPU usage when any Pod with a UDP port changes

## Issue Description
We are encountering a severe performance issue in kube-proxy (v1.32) when any Pod with a UDP port is updated (e.g., CoreDNS). In the new kube-proxy implementation, changes to Services or Pods that expose UDP ports trigger a full conntrack cleanup. This cleanup process iterates over the entire conntrack table, leading to extremely high resource consumption—sometimes up to 12 GB of memory and 1.5 CPU cores per kube-proxy instance.

In a simple test, we observed 2,780 instances of the log message "Adding conntrack filter for cleanup", which caused an OOM when kube-proxy was limited to 256 MB of memory. Without that limit, kube-proxy memory usage spiked to 12 GB. On nodes with large conntrack tables, kube-proxy effectively becomes stuck, consuming all available memory each time there is a UDP endpoint change.

This issue appears to be systemic; every change in a Pod with a UDP port triggers all kube-proxy instances to perform the extensive cleanup. Currently, there is no option to disable or throttle this behavior, which disrupts cluster stability and can lead to service degradation or outages. We request that the cleanup logic be revised to target only the relevant conntrack entries or that a mechanism be provided to disable or limit this aggressive cleanup behavior.

### What did you expect to happen?
We expected kube-proxy to handle conntrack cleanup in a more efficient and targeted way. Even if it needs to scan a significant portion of the conntrack table, it should do so without causing a spike to 12 GB of memory usage. Ideally, it would either:

- Limit its cleanup to entries relevant to the specific changed UDP endpoint.
- Provide a way to configure or disable this aggressive cleanup process so it does not risk out-of-memory (OOM) events or excessively high CPU usage.

### How can we reproduce it (as minimally and precisely as possible)?
- Deploy multiple Pods that generate a high volume of DNS requests, for example:
- A simple Golang application making repeated DNS lookups without any caching mechanism.
- Observe kube-proxy resource usage (memory and CPU) on that node.
- Delete or update the coredns Pod (which also uses UDP DNS).
- Watch the logs and resource usage of kube-proxy closely, noting the surge in memory (potentially up to 12 GB) and CPU usage as it performs the conntrack cleanup.

## Summary of Root Cause
The root cause is in the vishvananda/netlink library at `conntrack_linux.go#L175`. When kube-proxy performs conntrack cleanup for UDP endpoints, all flow entries for which the delete call fails are collected in an array. The bloating of this array as failed deletions accumulate is causing the memory spikes. This happens because the cleanup process iterates over the entire conntrack table for UDP port changes, and failures in deletion accumulate in memory rather than being handled efficiently.

## Link to Original Issue
https://github.com/kubernetes/kubernetes/issues/129982

