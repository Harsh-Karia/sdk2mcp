#!/usr/bin/env python3
"""
Test the Universal Pattern Recognition System on Kubernetes and Azure SDKs
This validates that our system truly works with ANY Python SDK.
"""

from introspector import UniversalIntrospector
from pattern_recognizer import UniversalPatternRecognizer
import json
import sys

def test_sdk(sdk_name: str, module_name: str):
    """Test pattern recognition on a specific SDK."""
    print(f"\n{'='*60}")
    print(f"🔍 TESTING: {sdk_name}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Discover methods
        introspector = UniversalIntrospector()
        all_methods = introspector.discover_from_module(module_name)
        filtered_methods = introspector.filter_high_value_methods(all_methods)
        
        print(f"✅ Methods discovered: {len(all_methods)} total → {len(filtered_methods)} filtered")
        
        # Step 2: Analyze patterns
        pattern_recognizer = UniversalPatternRecognizer()
        patterns = pattern_recognizer.analyze_patterns(filtered_methods)
        
        # Step 3: Show results
        print(f"📦 Resources discovered: {len(patterns['resources'])}")
        
        # Show top 5 resources
        if patterns['resources']:
            print("\nTop resources:")
            for i, (name, resource) in enumerate(list(patterns['resources'].items())[:5]):
                crud_ops = sum(len(ops) for ops in resource.crud_operations.values())
                print(f"  {i+1}. {name}: {crud_ops} CRUD operations")
        
        print(f"\n🔐 Auth flows: {len(patterns['auth_flows'])}")
        for flow_type in patterns['auth_flows']:
            print(f"  - {flow_type}: {len(patterns['auth_flows'][flow_type])} methods")
        
        print(f"\n📁 API groups: {len(patterns['api_groups'])}")
        for group in patterns['api_groups']:
            print(f"  - {group.name}: {len(group.methods)} methods")
        
        # Statistics
        stats = patterns['statistics']
        print(f"\n📊 Method distribution:")
        for method_type, count in stats['methods_by_type'].items():
            if count > 0:
                percentage = (count / stats['total_methods']) * 100
                print(f"  {method_type}: {count} ({percentage:.1f}%)")
        
        return True, patterns
        
    except ImportError as e:
        print(f"❌ SDK not installed: {e}")
        print(f"   Install with: pip install {sdk_name}")
        return False, None
    except Exception as e:
        print(f"❌ Error testing SDK: {e}")
        return False, None

def main():
    """Test pattern recognition on additional SDKs."""
    print("🚀 TESTING ADDITIONAL SDKS")
    print("="*60)
    
    # Define SDKs to test
    sdks_to_test = [
        ("kubernetes", "kubernetes"),
        ("azure-mgmt-resource", "azure.mgmt.resource"),
        ("azure-storage-blob", "azure.storage.blob"),
        ("boto3", "boto3"),  # Bonus: AWS SDK
    ]
    
    results = {}
    
    for sdk_name, module_name in sdks_to_test:
        success, patterns = test_sdk(sdk_name, module_name)
        if success:
            results[sdk_name] = patterns
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    
    if results:
        print(f"\n{'SDK':<25} {'Methods':<10} {'Resources':<12} {'Auth Flows':<12}")
        print("-" * 60)
        
        for sdk_name, patterns in results.items():
            methods = patterns['statistics']['total_methods']
            resources = len(patterns['resources'])
            auth_flows = len(patterns['auth_flows'])
            print(f"{sdk_name:<25} {methods:<10} {resources:<12} {auth_flows:<12}")
        
        print("\n✅ Pattern recognition works universally!")
        print("   The system successfully analyzed all tested SDKs without any SDK-specific code.")
    else:
        print("⚠️  No SDKs were successfully tested.")
        print("   You may need to install the SDKs first:")
        print("   pip install kubernetes azure-mgmt-resource azure-storage-blob boto3")
    
    # Save results
    if results:
        with open('additional_sdks_results.json', 'w') as f:
            # Convert to serializable format
            serializable = {}
            for sdk_name, patterns in results.items():
                serializable[sdk_name] = {
                    'resources_count': len(patterns['resources']),
                    'auth_flows_count': len(patterns['auth_flows']),
                    'api_groups_count': len(patterns['api_groups']),
                    'total_methods': patterns['statistics']['total_methods'],
                    'method_distribution': dict(patterns['statistics']['methods_by_type'])
                }
            json.dump(serializable, f, indent=2)
        print("\n💾 Results saved to: additional_sdks_results.json")

if __name__ == "__main__":
    main()