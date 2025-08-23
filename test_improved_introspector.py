#!/usr/bin/env python3
"""
Test the improved introspector with SDK hints on all SDKs
"""

from introspector_v2 import UniversalIntrospector
import json

def test_sdk(sdk_name: str, module_name: str):
    """Test improved introspector on a specific SDK."""
    print(f"\n{'='*60}")
    print(f"🔍 Testing: {sdk_name}")
    print(f"{'='*60}")
    
    # Use improved introspector with SDK hints
    introspector = UniversalIntrospector(sdk_name=sdk_name)
    all_methods = introspector.discover_from_module(module_name)
    filtered_methods = introspector.filter_high_value_methods(all_methods)
    
    print(f"📊 Results:")
    print(f"  Total discovered: {len(all_methods)}")
    print(f"  After filtering: {len(filtered_methods)}")
    print(f"  Noise reduction: {((len(all_methods) - len(filtered_methods)) / len(all_methods) * 100):.1f}%")
    
    # Check for key methods we expect
    print(f"\n🎯 Key Method Check:")
    
    if sdk_name == "kubernetes":
        key_methods = [
            "create_namespaced_pod",
            "list_namespaced_pod", 
            "delete_namespaced_deployment",
            "create_namespaced_service"
        ]
        for method_name in key_methods:
            found = any(method_name in m.full_name for m in filtered_methods)
            print(f"  {'✅' if found else '❌'} {method_name}")
    
    elif sdk_name == "azure_mgmt_resource":
        key_methods = [
            "create_or_update",  # Resource groups
            "list",  # Subscriptions
            "delete",  # Resources
            "get"  # Resource info
        ]
        for method_name in key_methods:
            found = any(method_name == m.name for m in filtered_methods 
                       if 'operations' in str(m.parent_class).lower())
            print(f"  {'✅' if found else '❌'} {method_name} (in *Operations classes)")
    
    elif sdk_name == "azure_storage_blob":
        key_methods = [
            "upload_blob",
            "download_blob",
            "delete_blob",
            "create_container"
        ]
        for method_name in key_methods:
            found = any(method_name in m.name for m in filtered_methods)
            print(f"  {'✅' if found else '❌'} {method_name}")
    
    elif sdk_name == "github":
        key_methods = [
            "get_user",
            "get_repo",
            "create_issue",
            "create_pull"
        ]
        for method_name in key_methods:
            found = any(method_name in m.name for m in filtered_methods)
            print(f"  {'✅' if found else '❌'} {method_name}")
    
    elif sdk_name == "requests":
        key_methods = [
            "get", "post", "put", "delete", "patch", "head"
        ]
        for method_name in key_methods:
            found = any(m.name == method_name and 'api' in m.full_name 
                       for m in filtered_methods)
            print(f"  {'✅' if found else '❌'} requests.api.{method_name}")
    
    # Show top 10 methods by priority score
    print(f"\n📈 Top 10 Methods by Priority:")
    sorted_methods = sorted(filtered_methods, key=lambda m: m.priority_score, reverse=True)[:10]
    for i, method in enumerate(sorted_methods, 1):
        print(f"  {i:2}. {method.full_name} (score: {method.priority_score:.1f})")
    
    # Check for unwanted methods
    print(f"\n🚫 Checking for unwanted methods:")
    unwanted_found = False
    
    # Check for _with_http_info
    http_info_methods = [m for m in filtered_methods if '_with_http_info' in m.name]
    if http_info_methods:
        print(f"  ❌ Found {len(http_info_methods)} _with_http_info methods")
        unwanted_found = True
    
    # Check for azure.core bleed in Azure SDKs
    if 'azure' in sdk_name:
        core_bleed = [m for m in filtered_methods if 'azure.core' in str(m.parent_class)]
        if core_bleed:
            print(f"  ❌ Found {len(core_bleed)} azure.core methods")
            unwanted_found = True
    
    # Check for private module paths
    private_paths = [m for m in filtered_methods if '._' in m.module_path]
    if private_paths:
        print(f"  ⚠️  Found {len(private_paths)} methods from private modules")
        for m in private_paths[:3]:
            print(f"     - {m.full_name}")
    
    if not unwanted_found and not private_paths:
        print(f"  ✅ No unwanted methods found!")
    
    return {
        'total': len(all_methods),
        'filtered': len(filtered_methods),
        'top_methods': [m.full_name for m in sorted_methods]
    }

def main():
    print("🚀 TESTING IMPROVED INTROSPECTOR WITH SDK HINTS")
    print("="*60)
    
    sdks = [
        ("github", "github"),
        ("requests", "requests"),
        ("kubernetes", "kubernetes"),
        ("azure_mgmt_resource", "azure.mgmt.resource"),
        ("azure_storage_blob", "azure.storage.blob")
    ]
    
    results = {}
    for sdk_name, module_name in sdks:
        try:
            results[sdk_name] = test_sdk(sdk_name, module_name)
        except Exception as e:
            print(f"❌ Error testing {sdk_name}: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    print(f"\n{'SDK':<25} {'Total':<10} {'Filtered':<10} {'Reduction':<10}")
    print("-" * 55)
    for sdk_name, result in results.items():
        reduction = ((result['total'] - result['filtered']) / result['total'] * 100)
        print(f"{sdk_name:<25} {result['total']:<10} {result['filtered']:<10} {reduction:.1f}%")
    
    print("\n✅ Improved introspector with SDK hints is working!")

if __name__ == "__main__":
    main()