#!/usr/bin/env python3
"""
Generate comprehensive JSON outputs for GitHub and requests SDKs
for final review by GPT/Claude.
"""

import json
from introspector import UniversalIntrospector


def generate_comprehensive_output(sdk_name: str, max_methods: int = 100):
    """Generate comprehensive introspection output for an SDK"""
    print(f"=" * 70)
    print(f"Generating Comprehensive Output for: {sdk_name}")
    print(f"=" * 70)
    
    introspector = UniversalIntrospector()
    
    # Discover all methods
    print(f"🔍 Discovering methods from {sdk_name}...")
    all_methods = introspector.discover_from_module(sdk_name)
    
    # Filter high-value methods
    filtered_methods = introspector.filter_high_value_methods(all_methods)
    
    print(f"📊 Results:")
    print(f"  Total methods discovered: {len(all_methods)}")
    print(f"  High-value methods: {len(filtered_methods)}")
    
    # Categorize methods for analysis
    operations = {
        'list/get': [],
        'create/add': [],
        'update/edit': [],
        'delete/remove': [],
        'search': [],
        'authentication': [],
        'other': []
    }
    
    for method in filtered_methods:
        name_lower = method.name.lower()
        categorized = False
        
        if 'auth' in name_lower or 'login' in name_lower or 'token' in name_lower:
            operations['authentication'].append(method)
            categorized = True
        elif 'list' in name_lower or 'get' in name_lower:
            operations['list/get'].append(method)
            categorized = True
        elif 'create' in name_lower or 'add' in name_lower or 'new' in name_lower:
            operations['create/add'].append(method)
            categorized = True
        elif 'update' in name_lower or 'edit' in name_lower or 'set' in name_lower or 'modify' in name_lower:
            operations['update/edit'].append(method)
            categorized = True
        elif 'delete' in name_lower or 'remove' in name_lower:
            operations['delete/remove'].append(method)
            categorized = True
        elif 'search' in name_lower or 'find' in name_lower:
            operations['search'].append(method)
            categorized = True
        
        if not categorized:
            operations['other'].append(method)
    
    # Print category summary
    print(f"\n📁 Method Categories:")
    for category, methods in operations.items():
        if methods:
            print(f"  {category}: {len(methods)} methods")
    
    # Get unique owner classes
    owners = set()
    for method in all_methods:
        if method.parent_class:
            owners.add(method.parent_class)
    
    print(f"\n🏛️  Classes discovered: {len(owners)}")
    if len(owners) <= 20:
        for owner in sorted(owners):
            print(f"    - {owner}")
    else:
        for owner in sorted(list(owners))[:10]:
            print(f"    - {owner}")
        print(f"    ... and {len(owners) - 10} more")
    
    # Create comprehensive output
    output = {
        'sdk': sdk_name,
        'introspection_summary': {
            'total_methods': len(all_methods),
            'high_value_methods': len(filtered_methods),
            'unique_classes': len(owners),
            'operations_breakdown': {k: len(v) for k, v in operations.items()}
        },
        'sample_by_category': {},
        'detailed_methods': introspector.to_dict(filtered_methods[:max_methods])
    }
    
    # Add samples from each category (first 5 from each) - USE FILTERED METHODS
    for category, methods in operations.items():
        if methods:
            output['sample_by_category'][category] = [
                {
                    'name': m.name,
                    'full_name': m.full_name,
                    'owner': m.parent_class,
                    'parameters': len(m.parameters),
                    'return_type': m.return_type,
                    'docstring': m.docstring[:100] + '...' if m.docstring and len(m.docstring) > 100 else m.docstring
                }
                for m in methods[:5]  # This is already from filtered_methods, so it's correct
            ]
    
    # Save to file
    filename = f"{sdk_name}_comprehensive_introspection.json"
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Comprehensive output saved to: {filename}")
    print(f"   File contains {max_methods} detailed method entries")
    
    return output


def main():
    """Generate comprehensive outputs for both SDKs"""
    print("🚀 Generating Final JSON Outputs for Phase 2 Review")
    print("=" * 70)
    
    # Generate GitHub SDK output
    github_output = generate_comprehensive_output('github', max_methods=150)
    
    print("\n")
    
    # Generate requests SDK output  
    requests_output = generate_comprehensive_output('requests', max_methods=100)
    
    print("\n" + "=" * 70)
    print("✅ Final JSON Generation Complete!")
    print("=" * 70)
    
    print("\n📊 Summary:")
    print(f"  GitHub SDK: {github_output['introspection_summary']['total_methods']} total methods")
    print(f"  requests SDK: {requests_output['introspection_summary']['total_methods']} total methods")
    
    print("\n📁 Files generated:")
    print("  - github_comprehensive_introspection.json")
    print("  - requests_comprehensive_introspection.json")
    
    print("\n🎯 Ready for GPT/Claude review!")
    print("These files contain:")
    print("  ✓ Complete method discovery statistics")
    print("  ✓ Categorized method breakdowns")
    print("  ✓ Sample methods from each category")
    print("  ✓ Detailed method information with parameters/types")
    print("  ✓ Owner/class context for all methods")


if __name__ == "__main__":
    main()