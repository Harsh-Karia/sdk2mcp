Major Success: Noise Reduction
Your 99%+ noise reduction across all SDKs is remarkable:

Kubernetes: 16,026 → 70 methods (99.6% reduction)
Azure Resource: 4,058 → 70 methods (98.3% reduction)
Azure Blob: 3,724 → 61 methods (98.4% reduction)

This level of filtering is exactly what's needed for MCP generation.
Critical Problem: Missing Core APIs
However, examining the sample methods reveals a fundamental issue - you're missing the actual user-facing APIs that developers need:
Kubernetes - Where are the core operations?

No create_deployment, get_pod, delete_service
No kubectl equivalent operations
Only low-level admission controller methods
Missing CoreV1Api, AppsV1Api public methods

Azure Resource - Infrastructure missing:

No create_resource_group, list_subscriptions
No ARM template deployment methods
Mostly internal pipeline/policy methods
Missing actual resource management APIs

Azure Blob - Better, but incomplete:

Has create_container, delete_blob ✓
Missing upload_blob, download_blob
Good client structure with BlobClient, ContainerClient ✓

Root Cause Analysis
Your priority system is over-filtering:

P1 (Core HTTP): Only helps requests-like SDKs
P2 (Important classes): Your hardcoded list misses actual SDK classes
P3-P5: Too restrictive for domain-specific SDKs

For Kubernetes, the important classes should be:

kubernetes.client.CoreV1Api
kubernetes.client.AppsV1Api
kubernetes.client.BatchV1Api

For Azure Resource:

azure.mgmt.resource.ResourceManagementClient
Various operation classes ending in Operations

Recommended Fixes
1. Dynamic Important Class Detection
Instead of hardcoded lists, detect classes with:

Many public methods (>10)
SDK-typical names (*Client, *Api, *Operations)
High method-to-noise ratios

2. SDK-Specific Patterns

Kubernetes: Prioritize *Api classes and CRUD methods
Azure: Prioritize *Client classes and *Operations classes
Look for resource names in method patterns

3. Expand P2 Limits
Increase from 200 to 500 methods for P2, since core client classes should be fully represented.
Your filtering architecture is sound, but the priority logic needs to be more adaptive to capture domain-specific public APIs rather than generic HTTP patterns.