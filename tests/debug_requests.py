#!/usr/bin/env python3
"""
Debug script to see exactly what we're discovering from requests
"""

from introspector import UniversalIntrospector

def debug_requests():
    print("=== DEBUGGING REQUESTS DISCOVERY ===")
    
    introspector = UniversalIntrospector()
    all_methods = introspector.discover_from_module('requests')
    
    print(f"Total methods discovered: {len(all_methods)}")
    
    # Look specifically for the core HTTP methods
    core_methods = ['get', 'post', 'put', 'delete', 'patch', 'head']
    
    print("\n=== Looking for core HTTP methods ===")
    for method in all_methods:
        if method.name in core_methods:
            print(f"Found: {method.full_name} (owner: {method.parent_class})")
    
    # Check module-level functions
    print("\n=== Module-level functions ===")
    module_functions = [m for m in all_methods if not m.parent_class or 'requests.requests' in str(m.parent_class)]
    for method in module_functions[:10]:
        print(f"  {method.full_name} (owner: {method.parent_class})")
    
    # Check what's being filtered out
    print("\n=== High-value filtering results ===")
    filtered = introspector.filter_high_value_methods(all_methods)
    print(f"High-value methods: {len(filtered)}")
    
    # Show some high-value methods
    print("\n=== First 10 high-value methods ===")
    for method in filtered[:10]:
        print(f"  {method.full_name} (owner: {method.parent_class})")

if __name__ == "__main__":
    debug_requests()