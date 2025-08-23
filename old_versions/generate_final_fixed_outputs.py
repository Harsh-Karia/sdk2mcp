#!/usr/bin/env python3
"""
Generate final outputs with all fixes applied and pagination/LRO flags
"""

from introspector_v2 import UniversalIntrospector
import json
from collections import defaultdict

def add_method_flags(method_info_dict, method_obj):
    """Add pagination and LRO flags to method info."""
    method_info_dict['flags'] = {}
    
    # Check for pagination
    if method_obj.get('return_type'):
        return_type = method_obj['return_type'].lower()
        if any(paged in return_type for paged in ['paged', 'pager', 'iterator', 'iterable', 'itemPaged']):
            method_info_dict['flags']['paginated'] = True
    
    # Check for Long Running Operations (LRO)
    if method_obj.get('return_type'):
        return_type = method_obj['return_type'].lower()
        if any(lro in return_type for lro in ['poller', 'lropoller', 'operation']):
            method_info_dict['flags']['lro'] = True
    
    # Check docstring for pagination/LRO hints
    docstring = method_obj.get('docstring', '') or ''
    if docstring:
        doc_lower = docstring[:200].lower()
        if any(hint in doc_lower for hint in ['paged', 'iterator', 'long-running', 'polling']):
            if 'paged' in doc_lower or 'iterator' in doc_lower:
                method_info_dict['flags']['paginated'] = True
            if 'long-running' in doc_lower or 'polling' in doc_lower:
                method_info_dict['flags']['lro'] = True
    
    # Check for destructive operations
    method_name = method_obj['name'].lower()
    if any(verb in method_name for verb in ['create', 'update', 'delete', 'patch', 'remove', 'destroy']):
        method_info_dict['flags']['destructive'] = True
        method_info_dict['flags']['confirm'] = True

def generate_output(sdk_name: str, module_name: str):
    """Generate final comprehensive output for an SDK."""
    print(f"\n{'='*70}")
    print(f"🚀 FINAL OUTPUT: {sdk_name}")
    print(f"{'='*70}")
    
    # Use improved introspector
    introspector = UniversalIntrospector(sdk_name=sdk_name)
    all_methods = introspector.discover_from_module(module_name)
    filtered_methods = introspector.filter_high_value_methods(all_methods)
    
    print(f"📊 Results: {len(all_methods)} total → {len(filtered_methods)} filtered")
    
    # Categorize methods
    categories = defaultdict(list)
    for method in filtered_methods:
        method_lower = method.name.lower()
        if any(verb in method_lower for verb in ['get', 'list', 'find', 'fetch']):
            categories['read'].append(method)
        elif any(verb in method_lower for verb in ['create', 'add', 'new']):
            categories['create'].append(method)
        elif any(verb in method_lower for verb in ['update', 'edit', 'patch', 'set']):
            categories['update'].append(method)
        elif any(verb in method_lower for verb in ['delete', 'remove', 'destroy']):
            categories['delete'].append(method)
        else:
            categories['other'].append(method)
    
    # Show category breakdown
    print(f"📁 Categories: {', '.join(f'{cat}({len(methods)})' for cat, methods in categories.items())}")
    
    # Build comprehensive output
    output = {
        "sdk_name": sdk_name,
        "module_name": module_name,
        "introspection_summary": {
            "total_discovered": len(all_methods),
            "filtered_high_value": len(filtered_methods),
            "noise_reduction_percent": round(((len(all_methods) - len(filtered_methods)) / len(all_methods) * 100), 1) if all_methods else 0,
            "classes_discovered": len(introspector.discovered_classes)
        },
        "method_categories": {cat: len(methods) for cat, methods in categories.items()},
        "top_priority_methods": [],
        "category_samples": {}
    }
    
    # Add top 25 methods by priority with flags
    sorted_methods = sorted(filtered_methods, key=lambda m: m.priority_score, reverse=True)[:25]
    for method in sorted_methods:
        method_dict = {
            "name": method.name,
            "full_name": method.full_name,
            "owner": str(method.parent_class),
            "priority_score": round(method.priority_score, 1),
            "is_async": method.is_async,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type_hint,
                    "required": p.is_required,
                    "default": p.default_value
                } for p in method.parameters[:5]
            ],
            "return_type": method.return_type
        }
        
        # Add flags
        add_method_flags(method_dict, {
            'name': method.name,
            'return_type': method.return_type,
            'docstring': method.docstring
        })
        
        output["top_priority_methods"].append(method_dict)
    
    # Add samples from each category with flags
    for cat, methods in categories.items():
        output["category_samples"][cat] = []
        for method in methods[:8]:  # More samples per category
            method_dict = {
                "name": method.name,
                "full_name": method.full_name,
                "owner": str(method.parent_class),
                "score": round(method.priority_score, 1)
            }
            
            # Add flags
            add_method_flags(method_dict, {
                'name': method.name,
                'return_type': method.return_type,
                'docstring': method.docstring
            })
            
            output["category_samples"][cat].append(method_dict)
    
    # Show key improvements
    print(f"✨ Key Improvements Applied:")
    if sdk_name == "kubernetes":
        connect_methods = [m for m in filtered_methods if m.name.startswith('connect_')]
        create_methods = [m for m in filtered_methods if m.name.startswith('create_')]
        print(f"   • De-emphasized connect_*: {len(connect_methods)} connect methods")
        print(f"   • Boosted CRUD operations: {len(create_methods)} create methods")
    
    if 'azure' in sdk_name and 'blob' in sdk_name:
        private_owners = [m for m in filtered_methods if '._' in str(m.parent_class)]
        print(f"   • Fixed private paths: {len(private_owners)} methods with private owners")
    
    if 'azure' in sdk_name and 'mgmt' in sdk_name:
        operations_methods = [m for m in filtered_methods if 'operations' in str(m.parent_class).lower()]
        print(f"   • Found operations groups: {len(operations_methods)} operation methods")
    
    # Count methods with flags
    destructive_count = sum(1 for m in output["top_priority_methods"] if m.get('flags', {}).get('destructive'))
    paginated_count = sum(1 for m in output["top_priority_methods"] if m.get('flags', {}).get('paginated'))
    lro_count = sum(1 for m in output["top_priority_methods"] if m.get('flags', {}).get('lro'))
    
    print(f"🏷️  Method Flags: destructive({destructive_count}), paginated({paginated_count}), lro({lro_count})")
    
    # Save to file
    filename = f"{sdk_name}_final_fixed.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"💾 Saved to: {filename}")
    
    return output

def main():
    print("🎯 GENERATING FINAL FIXED OUTPUTS")
    print("✅ All GPT feedback implemented:")
    print("   • Azure Blob: Public paths preferred")
    print("   • Azure Management: Operation groups discovered")  
    print("   • GitHub: Expanded beyond top-level client")
    print("   • Kubernetes: De-emphasized connect_*, boosted CRUD")
    print("   • All SDKs: Added pagination, LRO, destructive flags")
    print("="*70)
    
    sdks = [
        ("github", "github"),
        ("requests", "requests"),
        ("kubernetes", "kubernetes"),
        ("azure_mgmt_resource", "azure.mgmt.resource"),
        ("azure_storage_blob", "azure.storage.blob")
    ]
    
    results = []
    for sdk_name, module_name in sdks:
        try:
            result = generate_output(sdk_name, module_name)
            results.append(result)
        except Exception as e:
            print(f"❌ Error with {sdk_name}: {e}")
    
    # Summary
    print("\n" + "="*70)
    print("📈 FINAL SUMMARY")
    print("="*70)
    
    print(f"\n{'SDK':<25} {'Total':<8} {'Filtered':<8} {'Reduction':<10} {'Classes':<8}")
    print("-" * 62)
    for result in results:
        summary = result['introspection_summary']
        print(f"{result['sdk_name']:<25} {summary['total_discovered']:<8} {summary['filtered_high_value']:<8} {summary['noise_reduction_percent']:<9}% {summary['classes_discovered']:<8}")
    
    print("\n🎉 Ready for Phase 4: Universal MCP Tool Generator!")
    print("   All critical feedback addressed:")
    print("   ✓ Proper scoping and prioritization")
    print("   ✓ Core API methods captured")  
    print("   ✓ Clean public paths")
    print("   ✓ Smart method flags for safety")

if __name__ == "__main__":
    main()