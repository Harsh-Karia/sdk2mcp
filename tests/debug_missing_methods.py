#!/usr/bin/env python3
"""
Debug why get and head methods are missing
"""

from introspector import UniversalIntrospector

def debug_missing():
    print("=== DEBUGGING MISSING METHODS ===")
    
    introspector = UniversalIntrospector()
    all_methods = introspector.discover_from_module('requests')
    
    # Look for the missing methods in all_methods
    missing_methods = ['requests.api.get', 'requests.api.head']
    
    print("Looking for missing methods in all discovered methods:")
    for missing in missing_methods:
        found = [m for m in all_methods if m.full_name == missing]
        if found:
            method = found[0]
            print(f"✅ Found {missing}")
            print(f"  Owner: {method.parent_class}")
            print(f"  Is noise: {introspector._is_noise_method(method)}")
        else:
            print(f"❌ NOT FOUND: {missing}")
    
    # Check what api methods we do have
    print(f"\nAll requests.api methods found:")
    api_methods = [m for m in all_methods if 'requests.api.' in m.full_name and not 'sessions' in m.full_name]
    for method in api_methods:
        print(f"  {method.full_name} (is_noise: {introspector._is_noise_method(method)})")

if __name__ == "__main__":
    debug_missing()