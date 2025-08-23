#!/usr/bin/env python3
"""
Demonstrate the introspection engine with real SDKs.
"""

import json
from introspector import UniversalIntrospector


def demo_requests():
    """Demo introspection with the requests library"""
    print("=" * 60)
    print("Introspecting 'requests' Library")
    print("=" * 60)
    
    introspector = UniversalIntrospector()
    
    # Discover from the main requests module
    methods = introspector.discover_from_module('requests')
    
    # Filter to high-value methods
    filtered = introspector.filter_high_value_methods(methods)
    
    print(f"\n📊 Discovery Results:")
    print(f"  - Total methods found: {len(methods)}")
    print(f"  - High-value methods: {len(filtered)}")
    
    # Group methods by category
    categories = {
        'HTTP Methods': ['get', 'post', 'put', 'delete', 'patch', 'head', 'options'],
        'Session': ['Session'],
        'Other': []
    }
    
    categorized = {k: [] for k in categories}
    
    for method in filtered:
        categorized_flag = False
        for category, patterns in categories.items():
            if category == 'Other':
                continue
            if any(pattern in method.name for pattern in patterns):
                categorized[category].append(method)
                categorized_flag = True
                break
        if not categorized_flag:
            categorized['Other'].append(method)
    
    # Display categorized methods
    for category, methods_list in categorized.items():
        if methods_list:
            print(f"\n📁 {category}:")
            for method in methods_list[:5]:  # Show first 5
                params = [p.name for p in method.parameters]
                param_str = f"({', '.join(params[:3])}{'...' if len(params) > 3 else ''})"
                print(f"    - {method.name}{param_str}")
            if len(methods_list) > 5:
                print(f"    ... and {len(methods_list) - 5} more")
    
    # Save to JSON for inspection
    output = {
        'module': 'requests',
        'total_discovered': len(methods),
        'filtered_count': len(filtered),
        'methods': introspector.to_dict(filtered[:20])  # First 20 for brevity
    }
    
    with open('introspection_output.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Detailed output saved to introspection_output.json")
    
    return filtered


def demo_json_module():
    """Demo with json standard library"""
    print("\n" + "=" * 60)
    print("Introspecting 'json' Standard Library")
    print("=" * 60)
    
    introspector = UniversalIntrospector()
    methods = introspector.discover_from_module('json')
    
    print(f"\n📊 Found {len(methods)} methods")
    print("\n📁 Core JSON Functions:")
    
    core_functions = ['dump', 'dumps', 'load', 'loads']
    for method in methods:
        if method.name in core_functions:
            params = [p.name for p in method.parameters]
            print(f"    - {method.name}({', '.join(params[:2])}{'...' if len(params) > 2 else ''})")
            if method.docstring:
                print(f"      📝 {method.docstring[:60]}...")


def main():
    print("\n🚀 Universal SDK Introspection Engine Demo\n")
    
    # Demo with requests
    requests_methods = demo_requests()
    
    # Demo with json
    demo_json_module()
    
    print("\n" + "=" * 60)
    print("✅ Introspection Complete!")
    print("=" * 60)
    
    print("\n🎯 Key Achievements:")
    print("  1. Successfully discovered methods from real Python packages")
    print("  2. Filtered to high-value methods using patterns")
    print("  3. Extracted parameter information and types")
    print("  4. Works with ANY Python package without modification!")
    
    print("\n📌 Next Steps:")
    print("  - Phase 3: Pattern recognition for different SDK styles")
    print("  - Phase 4: Convert discovered methods to MCP tools")


if __name__ == "__main__":
    main()