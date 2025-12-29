# Issue #128638: kubelet crash: fatal error: concurrent map writes

## Issue Title
kubelet crash: fatal error: concurrent map writes

## Issue Description
While looking into three failing E2E tests in an AllAlpha job, Kubelet had crashed with the following error:

```
Nov 07 01:09:07.338827 bootstrap-e2e-minion-group-h288 kubelet[1937]: fatal error: concurrent map writes
Nov 07 01:09:07.342609 bootstrap-e2e-minion-group-h288 kubelet[1937]: goroutine 29497 [running]:
Nov 07 01:09:07.342609 bootstrap-e2e-minion-group-h288 kubelet[1937]: k8s.io/kubernetes/pkg/kubelet/cm/containermap.ContainerMap.Add(...)
```

This is a race condition causing a panic in the kubelet component.

## Summary of Root Cause
The root cause is that the `containerMap` is passed as a parameter to three managers, so it may be read/written by them concurrently without proper synchronization. The ContainerMap.Add() method is being called from multiple goroutines simultaneously, leading to concurrent map writes. This is a classic race condition where multiple goroutines attempt to modify the same map without proper locking or synchronization mechanisms.

## Link to Original Issue
https://github.com/kubernetes/kubernetes/issues/128638


