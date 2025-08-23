#!/usr/bin/env python3
"""
Generate comprehensive JSON outputs for Kubernetes and Azure SDKs
for manual review before proceeding to Phase 4.
"""

from introspector import UniversalIntrospector
from pattern_recognizer import UniversalPatternRecognizer
import json
from typing import List, Dict, Any
from collections import defaultdict

def generate_comprehensive_output(sdk_name: str, module_name: str):
    """Generate comprehensive introspection output for an SDK."""
    print(f"\n{'='*70}")
    print(f"Generating Comprehensive Output for: {sdk_name}")
    print(f"{'='*70}")
    
    try:
        # Discover methods
        introspector = UniversalIntrospector()
        all_methods = introspector.discover_from_module(module_name)
        filtered_methods = introspector.filter_high_value_methods(all_methods)
        
        print(f"🔍 Discovering methods from {module_name}...")
        print(f"📊 Results:")
        print(f"  Total methods discovered: {len(all_methods)}")
        print(f"  High-value methods: {len(filtered_methods)}")
        
        # Pattern recognition
        pattern_recognizer = UniversalPatternRecognizer()
        patterns = pattern_recognizer.analyze_patterns(filtered_methods)
        
        # Categorize methods for better understanding
        categories = defaultdict(list)
        for method in filtered_methods:
            method_lower = method.name.lower()
            if any(verb in method_lower for verb in ['get', 'list', 'find', 'search', 'fetch']):
                categories['list/get'].append(method)
            elif any(verb in method_lower for verb in ['create', 'add', 'new', 'make']):
                categories['create/add'].append(method)
            elif any(verb in method_lower for verb in ['update', 'edit', 'modify', 'patch', 'set']):
                categories['update/edit'].append(method)
            elif any(verb in method_lower for verb in ['delete', 'remove', 'destroy']):
                categories['delete/remove'].append(method)
            elif 'search' in method_lower:
                categories['search'].append(method)
            elif any(term in method_lower for term in ['auth', 'login', 'token', 'credential']):
                categories['authentication'].append(method)
            else:
                categories['other'].append(method)
        
        print(f"\n📁 Method Categories:")
        for category, methods in categories.items():
            if methods:
                print(f"  {category}: {len(methods)} methods")
        
        # Get unique classes
        unique_classes = set()
        for method in all_methods:
            if method.parent_class:
                unique_classes.add(str(method.parent_class))
        
        print(f"\n🏛️  Classes discovered: {len(unique_classes)}")
        # Show first 10 classes
        for i, cls in enumerate(sorted(unique_classes)[:10]):
            print(f"    - {cls}")
        if len(unique_classes) > 10:
            print(f"    ... and {len(unique_classes) - 10} more")
        
        # Build comprehensive output
        output = {
            "sdk_name": sdk_name,
            "module_name": module_name,
            "statistics": {
                "total_methods_discovered": len(all_methods),
                "high_value_methods": len(filtered_methods),
                "total_classes": len(unique_classes),
                "categories": {cat: len(methods) for cat, methods in categories.items() if methods}
            },
            "pattern_analysis": {
                "resources_discovered": len(patterns['resources']),
                "auth_flows": len(patterns['auth_flows']),
                "api_groups": len(patterns['api_groups']),
                "method_distribution": dict(patterns['statistics']['methods_by_type'])
            },
            "resources": {},
            "sample_methods": {},
            "classes": sorted(list(unique_classes))[:50]  # First 50 classes
        }
        
        # Add resource details
        for resource_name, resource in list(patterns['resources'].items())[:20]:  # Top 20 resources
            output["resources"][resource_name] = {
                "primary_class": resource.primary_class,
                "crud_operations": {
                    op_type: len(methods) 
                    for op_type, methods in resource.crud_operations.items() 
                    if methods
                },
                "auth_methods_count": len(resource.auth_methods),
                "relationships": resource.relationships[:5]
            }
        
        # Add sample methods from each category (max 100 total)
        sample_limit = 100
        samples_per_category = max(5, sample_limit // len(categories))
        
        for category, methods in categories.items():
            if methods:
                output["sample_methods"][category] = []
                for method in methods[:samples_per_category]:
                    method_info = {
                        "name": method.name,
                        "full_name": method.full_name,
                        "owner": str(method.parent_class) if method.parent_class else "module",
                        "is_async": method.is_async,
                        "parameters": [
                            {
                                "name": p.name,
                                "type": p.type_hint,
                                "required": p.is_required
                            } for p in method.parameters[:5]  # First 5 params
                        ],
                        "return_type": method.return_type
                    }
                    
                    # Add docstring preview if available
                    if method.docstring:
                        method_info["docstring_preview"] = method.docstring[:200]
                    
                    output["sample_methods"][category].append(method_info)
        
        # Save to file
        filename = f"{sdk_name.replace('-', '_')}_comprehensive_introspection.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        total_samples = sum(len(methods) for methods in output["sample_methods"].values())
        print(f"\n💾 Comprehensive output saved to: {filename}")
        print(f"   File contains {total_samples} detailed method entries")
        
        return output
        
    except Exception as e:
        print(f"❌ Error generating output for {sdk_name}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Generate comprehensive outputs for Kubernetes and Azure SDKs."""
    print("🚀 Generating Comprehensive JSON Outputs for Additional SDKs")
    print("="*70)
    
    sdks = [
        ("kubernetes", "kubernetes"),
        ("azure_mgmt_resource", "azure.mgmt.resource"),
        ("azure_storage_blob", "azure.storage.blob")
    ]
    
    results = []
    for sdk_name, module_name in sdks:
        output = generate_comprehensive_output(sdk_name, module_name)
        if output:
            results.append(output)
    
    # Generate summary
    print("\n" + "="*70)
    print("✅ JSON Generation Complete!")
    print("="*70)
    
    print("\n📊 Summary:")
    for result in results:
        print(f"  {result['sdk_name']}: {result['statistics']['total_methods_discovered']} total methods")
    
    print("\n📁 Files generated:")
    for sdk_name, _ in sdks:
        filename = f"{sdk_name.replace('-', '_')}_comprehensive_introspection.json"
        print(f"  - {filename}")
    
    print("\n🎯 Ready for review!")
    print("These files contain:")
    print("  ✓ Complete method discovery statistics")
    print("  ✓ Pattern recognition analysis")
    print("  ✓ Resource discovery with CRUD operations")
    print("  ✓ Sample methods from each category")
    print("  ✓ Class hierarchy information")

if __name__ == "__main__":
    main()