#!/usr/bin/env python3
"""
Debug Azure Management SDK discovery
"""

import azure.mgmt.resource
import inspect

print("Testing Azure Management module structure...")

# Check main module
print(f"\nModule: {azure.mgmt.resource}")
print(f"Module file: {azure.mgmt.resource.__file__}")

# Look for client classes
for name, obj in inspect.getmembers(azure.mgmt.resource, inspect.isclass):
    if 'Client' in name:
        print(f"\nFound client: {name}")
        print(f"  Full name: {obj.__module__}.{obj.__name__}")
        
        # Try to inspect attributes (operation groups)
        try:
            # Get all attributes that don't start with _
            attrs = [attr for attr in dir(obj) if not attr.startswith('_')]
            print(f"  Attributes: {attrs}")
            
            # Look for likely operation groups
            for attr in attrs:
                if attr not in ['models', 'close', 'send_request']:
                    print(f"    - {attr}: might be operation group")
        except Exception as e:
            print(f"  Error inspecting: {e}")

# Check submodules
try:
    from azure.mgmt.resource import resources
    print(f"\n✅ Found resources submodule")
    
    # Look for operations classes
    for name, obj in inspect.getmembers(resources, inspect.isclass):
        if 'Operations' in name:
            print(f"  Operations class: {name}")
            methods = [m for m, _ in inspect.getmembers(obj) if not m.startswith('_')]
            print(f"    Methods: {len(methods)} public methods")
            
except ImportError as e:
    print(f"❌ No resources submodule: {e}")

try:
    from azure.mgmt.resource import deployments
    print(f"\n✅ Found deployments submodule")
except ImportError as e:
    print(f"❌ No deployments submodule: {e}")