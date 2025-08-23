#!/usr/bin/env python3
"""
Verify that we're capturing the core HTTP API methods
"""

from introspector import UniversalIntrospector

def verify_core_api():
    print("=== VERIFYING CORE API CAPTURE ===")
    
    introspector = UniversalIntrospector()
    all_methods = introspector.discover_from_module('requests')
    filtered_methods = introspector.filter_high_value_methods(all_methods)
    
    print(f"Total methods: {len(all_methods)}")
    print(f"Filtered methods: {len(filtered_methods)}")
    
    # Check for core HTTP methods we MUST have
    core_api_methods = [
        'requests.api.get',
        'requests.api.post', 
        'requests.api.put',
        'requests.api.delete',
        'requests.api.patch',
        'requests.api.head'
    ]
    
    print("\n=== Core API Method Check ===")
    found_count = 0
    for expected in core_api_methods:
        found = any(m.full_name == expected for m in filtered_methods)
        status = "✅" if found else "❌"
        print(f"{status} {expected}")
        if found:
            found_count += 1
    
    print(f"\nFound {found_count}/{len(core_api_methods)} core API methods")
    
    # Show what we actually got in the delete/remove category
    print("\n=== Delete/Remove Category ===")
    for method in filtered_methods:
        if 'delete' in method.name.lower() or 'remove' in method.name.lower():
            print(f"  {method.full_name}")
    
    # Show what we got in list/get category  
    print("\n=== List/Get Category (first 10) ===")
    get_methods = [m for m in filtered_methods if 'get' in m.name.lower() or 'list' in m.name.lower()]
    for method in get_methods[:10]:
        print(f"  {method.full_name}")

if __name__ == "__main__":
    verify_core_api()