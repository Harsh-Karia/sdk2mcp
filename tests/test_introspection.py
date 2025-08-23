#!/usr/bin/env python3
"""
Test the Universal SDK Introspection Engine with various SDK patterns.
"""

import json
import sys
from introspector import UniversalIntrospector, MethodInfo


def test_stdlib_module():
    """Test with a standard library module to verify basic functionality"""
    print("\n=== Testing with os.path module ===")
    introspector = UniversalIntrospector()
    
    # Test with os.path (simple module with functions)
    methods = introspector.discover_from_module('os.path')
    
    # Filter to just show a few interesting ones
    interesting = [m for m in methods if m.name in ['join', 'exists', 'dirname', 'basename']]
    
    print(f"Found {len(methods)} total methods")
    print(f"Sample methods from os.path:")
    for method in interesting[:5]:
        params = [p.name for p in method.parameters]
        print(f"  - {method.name}({', '.join(params)})")
    
    return len(methods) > 0


def test_json_module():
    """Test with json module (has classes and functions)"""
    print("\n=== Testing with json module ===")
    introspector = UniversalIntrospector()
    
    methods = introspector.discover_from_module('json')
    
    # Look for key methods
    key_methods = ['loads', 'dumps', 'load', 'dump']
    found = [m for m in methods if any(key in m.name for key in key_methods)]
    
    print(f"Found {len(methods)} total methods")
    print("Key JSON methods discovered:")
    for method in found:
        print(f"  - {method.full_name}")
    
    return len(found) > 0


def test_with_real_sdk():
    """Test with a real SDK if available"""
    print("\n=== Testing with Real SDKs (if installed) ===")
    introspector = UniversalIntrospector()
    
    # Try different SDKs that might be installed
    test_sdks = [
        ('github', 'Github'),  # PyGithub
        ('kubernetes.client', 'CoreV1Api'),  # kubernetes
        ('stripe', 'Customer'),  # stripe
        ('requests', 'Session'),  # requests (common)
    ]
    
    for module_name, class_name in test_sdks:
        try:
            # Try to import and introspect
            module = __import__(module_name, fromlist=[class_name])
            if hasattr(module, class_name):
                cls = getattr(module, class_name)
                methods = introspector.discover_from_class(cls, f"{module_name}.{class_name}")
                
                if methods:
                    print(f"\n✓ {module_name}.{class_name}: Found {len(methods)} methods")
                    # Show first few methods
                    for method in methods[:3]:
                        print(f"    - {method.name}")
                    if len(methods) > 3:
                        print(f"    ... and {len(methods) - 3} more")
        except ImportError:
            print(f"✗ {module_name}: Not installed (skip)")
        except Exception as e:
            print(f"✗ {module_name}: Error - {e}")


def test_pattern_detection():
    """Test our ability to identify high-value methods"""
    print("\n=== Testing Pattern Detection ===")
    introspector = UniversalIntrospector()
    
    # Create mock method info for testing
    mock_methods = [
        MethodInfo("list_users", "api.list_users", [], None, None, False, False, False, None),
        MethodInfo("get_user", "api.get_user", [], None, None, False, False, False, None),
        MethodInfo("_internal_helper", "api._internal_helper", [], None, None, False, False, False, None),
        MethodInfo("create_resource", "api.create_resource", [], None, None, False, False, False, None),
        MethodInfo("__init__", "api.__init__", [], None, None, False, False, False, None),
        MethodInfo("update_settings", "api.update_settings", [], None, None, False, False, False, None),
        MethodInfo("delete_item", "api.delete_item", [], None, None, False, False, False, None),
        MethodInfo("helper_function_xyz", "api.helper_function_xyz", [], None, None, False, False, False, None),
    ]
    
    # Filter using our patterns
    introspector.discovered_methods = mock_methods
    filtered = introspector.filter_high_value_methods(mock_methods)
    
    print(f"Original methods: {len(mock_methods)}")
    print(f"Filtered methods: {len(filtered)}")
    print("High-value methods identified:")
    for method in filtered:
        print(f"  - {method.name}")
    
    # Should have filtered out _internal_helper and __init__
    assert "_internal_helper" not in [m.name for m in filtered]
    assert "__init__" not in [m.name for m in filtered]
    
    return True


def test_method_details():
    """Test extraction of method details"""
    print("\n=== Testing Method Detail Extraction ===")
    
    # Define a test class
    class TestAPI:
        """A test API class"""
        
        def simple_method(self):
            """A simple method with no parameters"""
            pass
        
        def method_with_params(self, name: str, age: int = 0, active: bool = True):
            """A method with typed parameters and defaults"""
            return f"{name} is {age} years old"
        
        async def async_method(self, data: dict) -> str:
            """An async method"""
            return "async result"
        
        @staticmethod
        def static_method(value: float) -> float:
            """A static method"""
            return value * 2
    
    introspector = UniversalIntrospector()
    methods = introspector.discover_from_class(TestAPI, "test.TestAPI")
    
    print(f"Discovered {len(methods)} methods from TestAPI:")
    
    for method in methods:
        print(f"\n  {method.name}:")
        print(f"    - Async: {method.is_async}")
        print(f"    - Static: {method.is_static}")
        print(f"    - Parameters: {len(method.parameters)}")
        for param in method.parameters:
            print(f"      * {param.name}: {param.type_hint or 'Any'} {'(required)' if param.is_required else f'(default: {param.default_value})'}")
        if method.return_type:
            print(f"    - Returns: {method.return_type}")
    
    return len(methods) >= 3


def main():
    """Run all tests"""
    print("=" * 60)
    print("Testing Universal SDK Introspection Engine")
    print("=" * 60)
    
    tests = [
        ("Standard Library Module", test_stdlib_module),
        ("JSON Module", test_json_module),
        ("Pattern Detection", test_pattern_detection),
        ("Method Details", test_method_details),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
                failed += 1
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
            failed += 1
    
    # Also run real SDK test (doesn't count toward pass/fail)
    test_with_real_sdk()
    
    print("\n" + "=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✅ All tests passed! Introspection engine is working.")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())