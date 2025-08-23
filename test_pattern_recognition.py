#!/usr/bin/env python3
"""
Test the Universal Pattern Recognition System on GitHub and requests SDKs
"""

from introspector import UniversalIntrospector
from pattern_recognizer import UniversalPatternRecognizer
import json
from pprint import pprint

def test_pattern_recognition(sdk_name: str):
    """Test pattern recognition on a specific SDK."""
    print(f"\n{'='*60}")
    print(f"🔍 TESTING PATTERN RECOGNITION: {sdk_name.upper()}")
    print(f"{'='*60}")
    
    # Step 1: Discover methods
    introspector = UniversalIntrospector()
    all_methods = introspector.discover_from_module(sdk_name)
    filtered_methods = introspector.filter_high_value_methods(all_methods)
    
    print(f"📊 Methods: {len(all_methods)} total → {len(filtered_methods)} filtered")
    
    # Step 2: Analyze patterns
    pattern_recognizer = UniversalPatternRecognizer()
    patterns = pattern_recognizer.analyze_patterns(filtered_methods)
    
    # Step 3: Display results
    print(f"\n🏛️  DISCOVERED RESOURCES ({len(patterns['resources'])})")
    print("-" * 40)
    for resource_name, resource in patterns['resources'].items():
        print(f"📦 {resource_name.upper()}")
        print(f"   Primary Class: {resource.primary_class}")
        
        # Show CRUD operations
        crud_summary = []
        for op_type, methods in resource.crud_operations.items():
            if methods:
                crud_summary.append(f"{op_type}({len(methods)})")
        
        if crud_summary:
            print(f"   CRUD: {', '.join(crud_summary)}")
        
        if resource.auth_methods:
            print(f"   Auth: {len(resource.auth_methods)} methods")
        
        if resource.relationships:
            print(f"   Related: {', '.join(resource.relationships[:3])}")
        print()
    
    print(f"\n🔐 AUTHENTICATION FLOWS ({len(patterns['auth_flows'])})")
    print("-" * 40)
    for flow_type, methods in patterns['auth_flows'].items():
        print(f"🔑 {flow_type}: {len(methods)} methods")
        for method in methods[:3]:  # Show first 3
            print(f"   - {method.name}")
        if len(methods) > 3:
            print(f"   ... and {len(methods) - 3} more")
    
    print(f"\n📁 API GROUPS ({len(patterns['api_groups'])})")
    print("-" * 40)
    for group in patterns['api_groups']:
        print(f"📋 {group.name}: {len(group.methods)} methods ({group.resource_type})")
        print(f"   {group.description}")
        
        # Show sample methods
        for method in group.methods[:3]:
            print(f"   - {method.name}")
        if len(group.methods) > 3:
            print(f"   ... and {len(group.methods) - 3} more")
        print()
    
    print(f"\n📊 STATISTICS")
    print("-" * 40)
    stats = patterns['statistics']
    print(f"Total methods analyzed: {stats['total_methods']}")
    print(f"Classes analyzed: {stats['classes_analyzed']}")
    
    print("\nMethod distribution:")
    for method_type, count in stats['methods_by_type'].items():
        percentage = (count / stats['total_methods']) * 100
        print(f"   {method_type}: {count} ({percentage:.1f}%)")
    
    return patterns

def main():
    """Test pattern recognition on both SDKs."""
    print("🚀 UNIVERSAL PATTERN RECOGNITION TESTING")
    print("="*60)
    
    # Test on requests SDK
    requests_patterns = test_pattern_recognition('requests')
    
    # Test on GitHub SDK
    github_patterns = test_pattern_recognition('github')
    
    # Summary comparison
    print(f"\n{'='*60}")
    print("📈 COMPARISON SUMMARY")
    print(f"{'='*60}")
    
    print(f"{'Metric':<25} {'requests':<15} {'github':<15}")
    print("-" * 55)
    print(f"{'Resources discovered':<25} {len(requests_patterns['resources']):<15} {len(github_patterns['resources']):<15}")
    print(f"{'Auth flows':<25} {len(requests_patterns['auth_flows']):<15} {len(github_patterns['auth_flows']):<15}")
    print(f"{'API groups':<25} {len(requests_patterns['api_groups']):<15} {len(github_patterns['api_groups']):<15}")
    print(f"{'Total methods':<25} {requests_patterns['statistics']['total_methods']:<15} {github_patterns['statistics']['total_methods']:<15}")
    
    # Save detailed results to JSON
    results = {
        'requests': requests_patterns,
        'github': github_patterns
    }
    
    # Convert MethodInfo objects to dicts for JSON serialization
    def serialize_patterns(patterns):
        serialized = {}
        
        # Serialize resources
        serialized['resources'] = {}
        for name, resource in patterns['resources'].items():
            serialized['resources'][name] = {
                'name': resource.name,
                'primary_class': resource.primary_class,
                'relationships': resource.relationships,
                'crud_operations': {
                    op_type: [{'name': m.name, 'full_name': m.full_name} for m in methods]
                    for op_type, methods in resource.crud_operations.items()
                },
                'auth_methods': [{'name': m.name, 'full_name': m.full_name} for m in resource.auth_methods]
            }
        
        # Serialize API groups
        serialized['api_groups'] = []
        for group in patterns['api_groups']:
            serialized['api_groups'].append({
                'name': group.name,
                'description': group.description,
                'resource_type': group.resource_type,
                'methods': [{'name': m.name, 'full_name': m.full_name} for m in group.methods]
            })
        
        # Serialize auth flows
        serialized['auth_flows'] = {}
        for flow_type, methods in patterns['auth_flows'].items():
            serialized['auth_flows'][flow_type] = [{'name': m.name, 'full_name': m.full_name} for m in methods]
        
        # Copy statistics as-is
        serialized['statistics'] = dict(patterns['statistics'])
        
        return serialized
    
    serialized_results = {
        'requests': serialize_patterns(requests_patterns),
        'github': serialize_patterns(github_patterns)
    }
    
    with open('pattern_recognition_results.json', 'w') as f:
        json.dump(serialized_results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: pattern_recognition_results.json")
    print("✅ Pattern recognition testing complete!")

if __name__ == "__main__":
    main()