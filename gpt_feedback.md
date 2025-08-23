Azure Storage Blob — strong, just de-dup & mark pagination/LRO

You’re surfacing the right clients and verbs (create/delete/get on BlobClient/BlobServiceClient/ContainerClient). ✅ 

But your owners are coming from private modules (e.g., azure.storage.blob._blob_client.BlobClient). Prefer public paths for tool IDs; keep private paths only internally for invocation. 

Add paginated: true to list/find methods (e.g., list_page_ranges, find_blobs_by_tags) and destructive: true to delete_*. If you detect pollers anywhere, set lro: true. 

Why this matters: cleaner tool IDs, safer defaults, and predictable outputs for agents.

Azure Mgmt (Resource) — scoping is now too narrow

Only 17 discovered / 16 kept, and the top items are mostly list_operations, close, models, _get_api_version on various client classes—not the operation groups users actually call (e.g., ResourceGroupsOperations, DeploymentsOperations). 

Fix: keep root scoping to azure.mgmt.resource., but boost owners that match \.operations\., and walk operation-group attributes on the main clients to collect methods like resource_groups.list, resource_groups.create_or_update, deployments.begin_create_or_update, etc. (No per-SDK code—just a generic “owner name contains .operations.” boost.) Then mark ItemPaged as paginated and LROPoller as lro. 

Why this matters: reviewers will try RG/Deployment calls first; this puts them front and center.

GitHub — clean slice, but expand beyond the top-level client

You’ve got a tidy set (72/67) with many Github.get_* and search_* methods—great for read/search. 

Missing bread-and-butter writes (e.g., Repository.create_issue, Repository.create_file, AuthenticatedUser.create_gist). Add a boost for owners named Repository|Issue|PullRequest|AuthenticatedUser, and prefer methods with :calls: hints or names starting with create|update|delete. Also treat sentinel defaults like NotSet as omittable. 

Why this matters: you’ll cover common workflows without sacrificing generality.

Kubernetes — de-emphasize connect_*, promote Core/Apps verbs

“Top methods” are dominated by connect_* (proxy/exec/portforward). Useful, but not what evaluators try first. Boost list|read|get|create|patch|replace|delete on CoreV1Api/AppsV1Api, and penalize names starting with connect_ so list_namespaced_pod, create_namespaced_deployment, etc., float to the top. Also exclude *_with_http_info and ensure deletes aren’t categorized as “update”. 

Why this matters: makes your K8s catalog feel “complete” at a glance.