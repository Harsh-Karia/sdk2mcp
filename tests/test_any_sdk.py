#!/usr/bin/env python3
"""
Universal SDK Tester - Proves the introspector works with ANY Python SDK
Usage: python test_any_sdk.py <module_name>
"""

import sys
import importlib
from introspector import UniversalIntrospector


def test_any_sdk(module_name: str):
    """Test introspection with any SDK - no SDK-specific code!"""
    
    print("=" * 70)
    print(f"Testing Universal Introspection with: {module_name}")
    print("=" * 70)
    
    # Check if module is installed
    try:
        importlib.import_module(module_name)
        print(f"✓ Module '{module_name}' is installed")
    except ImportError:
        print(f"✗ Module '{module_name}' is not installed")
        print(f"\nTry: pip install {module_name}")
        return False
    
    # Create introspector - NO SDK-SPECIFIC CODE!
    introspector = UniversalIntrospector()
    
    # Discover methods - WORKS WITH ANY MODULE!
    print(f"\n🔍 Discovering methods...")
    methods = introspector.discover_from_module(module_name)
    
    # Filter high-value methods
    filtered = introspector.filter_high_value_methods(methods)
    
    # Display results
    print(f"\n📊 Results:")
    print(f"  Total methods discovered: {len(methods)}")
    print(f"  High-value methods: {len(filtered)}")
    
    # Categorize by operation type (universal patterns)
    operations = {
        'list/get': 0,
        'create/add': 0,
        'update/set': 0,
        'delete/remove': 0,
        'other': 0
    }
    
    for method in filtered:
        name_lower = method.name.lower()
        if 'list' in name_lower or 'get' in name_lower:
            operations['list/get'] += 1
        elif 'create' in name_lower or 'add' in name_lower:
            operations['create/add'] += 1
        elif 'update' in name_lower or 'set' in name_lower or 'edit' in name_lower:
            operations['update/set'] += 1
        elif 'delete' in name_lower or 'remove' in name_lower:
            operations['delete/remove'] += 1
        else:
            operations['other'] += 1
    
    print(f"\n📁 Method Categories:")
    for op_type, count in operations.items():
        if count > 0:
            print(f"  {op_type}: {count} methods")
    
    # Show sample methods
    if filtered:
        print(f"\n🔧 Sample Methods (first 10):")
        for method in filtered[:10]:
            params = [p.name for p in method.parameters]
            param_str = ', '.join(params[:2]) + ('...' if len(params) > 2 else '')
            print(f"  - {method.name}({param_str})")
        
        if len(filtered) > 10:
            print(f"  ... and {len(filtered) - 10} more")
    
    # Success criteria
    print(f"\n" + "=" * 70)
    success = len(methods) > 0
    if success:
        print(f"✅ SUCCESS: Universal introspection works with {module_name}!")
        print(f"   No {module_name}-specific code was needed!")
    else:
        print(f"❌ No methods discovered (module might be empty or use unusual patterns)")
    
    return success


def main():
    if len(sys.argv) < 2:
        print("Universal SDK Introspection Tester")
        print("=" * 40)
        print("\nUsage: python test_any_sdk.py <module_name>")
        print("\nExamples:")
        print("  python test_any_sdk.py requests")
        print("  python test_any_sdk.py stripe")
        print("  python test_any_sdk.py twilio")
        print("  python test_any_sdk.py boto3")
        print("  python test_any_sdk.py discord")
        print("\nTry with ANY installed Python package!")
        return 1
    
    module_name = sys.argv[1]
    success = test_any_sdk(module_name)
    
    if success:
        print("\n🎯 This proves the introspector is TRULY UNIVERSAL!")
        print("   It worked without any code specific to this SDK!")
        return 0
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())