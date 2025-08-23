#!/usr/bin/env python3
"""
Debug Kubernetes discovery issue
"""

import kubernetes
import inspect

print("Testing Kubernetes module structure...")

# Check what's in the main module
print("\nMain kubernetes module members:")
for name, obj in inspect.getmembers(kubernetes)[:10]:
    print(f"  {name}: {type(obj)}")

# Check for client submodule
try:
    from kubernetes import client
    print("\n✅ kubernetes.client exists")
    
    # Check for API classes
    print("\nLooking for API classes:")
    api_classes = []
    for name, obj in inspect.getmembers(client):
        if inspect.isclass(obj) and 'Api' in name:
            api_classes.append(name)
    
    print(f"Found {len(api_classes)} API classes")
    for cls in api_classes[:10]:
        print(f"  - {cls}")
    
    # Check CoreV1Api specifically
    if hasattr(client, 'CoreV1Api'):
        print("\n✅ CoreV1Api found!")
        core_api = client.CoreV1Api
        
        # Count methods
        methods = [m for m, _ in inspect.getmembers(core_api) if not m.startswith('_')]
        print(f"  CoreV1Api has {len(methods)} public methods")
        
        # Show some key methods
        key_methods = [m for m in methods if any(k in m for k in ['create', 'list', 'delete', 'get'])]
        print(f"  Key methods ({len(key_methods)} total):")
        for m in key_methods[:5]:
            print(f"    - {m}")
    
except ImportError as e:
    print(f"❌ Error importing kubernetes.client: {e}")

# Check the module path
print(f"\nKubernetes module file: {kubernetes.__file__}")
print(f"Kubernetes module name: {kubernetes.__name__}")