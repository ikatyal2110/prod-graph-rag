# Issue #128709: If one enables PodLogsQuerySplitStreams and aims to access logs without stream, a validation error occurs

## Issue Title
If one enables PodLogsQuerySplitStreams and aims to access logs without stream, a validation error occurs

## Issue Description
This issue was observed in alpha jobs. When the PodLogsQuerySplitStreams feature gate is enabled, attempting to access pod logs without specifying a stream parameter results in a validation error:

```
The PodLogOptions "example" is invalid: stream: Required value: must be specified
```

### What happened?
We saw this in our alpha jobs during testing of the PodLogsQuerySplitStreams feature.

### What did you expect to happen?
One should be able to run the following command with this feature gate on:

```
k get --raw /api/v1/namespaces/default/pods/example/log
```

However, this command fails with a validation error requiring the stream parameter to be specified.

### How can we reproduce it (as minimally and precisely as possible)?
Start a cluster with PodLogsQuerySplitStreams enabled and attempt to access pod logs without specifying the stream parameter.

## Summary of Root Cause
When the PodLogsQuerySplitStreams feature gate is enabled, the validation logic incorrectly requires the stream parameter even when it should be optional for backward compatibility. The feature gate implementation changed the validation requirements but did not properly handle the case where logs are accessed without explicitly specifying a stream, breaking existing API usage patterns.

## Link to Original Issue
https://github.com/kubernetes/kubernetes/issues/128709


