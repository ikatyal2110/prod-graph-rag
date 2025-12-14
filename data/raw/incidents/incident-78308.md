# Issue #78308: CVE-2019-11245: container uid changes to root after first restart or if image is already pulled to the node

## Issue Title
CVE-2019-11245: container uid changes to root after first restart or if image is already pulled to the node

## Issue Description
CVSS:3.0/AV:L/AC:H/PR:N/UI:N/S:U/C:L/I:L/A:L, 4.9 (medium)

In kubelet v1.13.6 and v1.14.2, containers for pods that do not specify an explicit `runAsUser` attempt to run as uid 0 (root) on container restart, or if the image was previously pulled to the node. If the pod specified `mustRunAsNonRoot: true`, the kubelet will refuse to start the container as root. If the pod did not specify `mustRunAsNonRoot: true`, the kubelet will run the container as uid 0.

This is a security vulnerability (CVE-2019-11245) that allows containers to run with elevated privileges (root) when they should not, particularly on container restart or when images are pre-pulled.

## Summary of Root Cause
The root cause is a bug in the kubelet's container runtime handling logic. When a container is restarted or when an image was already pulled to the node, the kubelet incorrectly determines the user ID to run the container. Instead of properly inheriting or computing the correct non-root user ID from the pod specification or image metadata, it defaults to uid 0 (root). This occurs because the kubelet's logic for determining the container user ID has a flaw in handling these specific scenarios (restart and pre-pulled images), bypassing the normal security checks that would prevent running as root.

## Link to Original Issue
https://github.com/kubernetes/kubernetes/issues/78308

