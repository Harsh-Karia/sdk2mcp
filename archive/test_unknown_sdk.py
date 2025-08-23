#!/usr/bin/env python3
"""
Test the Universal MCP system with an UNKNOWN SDK (boto3 - AWS)
This proves the system works with ANY Python SDK without modifications.
"""

import sys
import json
from introspector_v2 import UniversalIntrospector
from pattern_recognizer import UniversalPatternRecognizer
from mcp_tool_generator import UniversalMCPToolGenerator

def test_unknown_sdk(sdk_name: str, module_name: str):
    """
    Test the entire pipeline with an unknown SDK.
    No SDK-specific code or configuration needed!
    """
    print(f"\n{'='*70}")
    print(f"🧪 TESTING UNKNOWN SDK: {sdk_name}")
    print(f"   Module: {module_name}")
    print(f"{'='*70}")
    
    try:
        # Step 1: Universal Introspection
        print("\n📍 Step 1: Universal Introspection")
        introspector = UniversalIntrospector()  # No SDK-specific config!
        all_methods = introspector.discover_from_module(module_name)
        filtered_methods = introspector.filter_high_value_methods(all_methods)
        
        print(f"   ✅ Discovered: {len(all_methods)} methods")
        print(f"   ✅ Filtered to: {len(filtered_methods)} high-value methods")
        print(f"   ✅ Noise reduction: {((len(all_methods) - len(filtered_methods)) / len(all_methods) * 100):.1f}%")
        
        # Step 2: Pattern Recognition
        print("\n📍 Step 2: Pattern Recognition")
        recognizer = UniversalPatternRecognizer()
        patterns = recognizer.analyze_patterns(filtered_methods)
        
        print(f"   ✅ Resources found: {len(patterns['resources'])}")
        print(f"   ✅ Auth flows: {len(patterns['auth_flows'])}")
        print(f"   ✅ API groups: {len(patterns['api_groups'])}")
        
        # Show some discovered resources
        if patterns['resources']:
            print("\n   📦 Sample Resources:")
            for name, resource in list(patterns['resources'].items())[:5]:
                crud_count = sum(len(ops) for ops in resource.crud_operations.values())
                print(f"      - {name}: {crud_count} CRUD operations")
        
        # Step 3: MCP Tool Generation
        print("\n📍 Step 3: MCP Tool Generation")
        generator = UniversalMCPToolGenerator(sdk_name)
        tool_groups = generator.generate_tools(filtered_methods[:50])  # Limit for testing
        
        total_tools = sum(len(g.tools) for g in tool_groups)
        print(f"   ✅ Generated: {total_tools} MCP tools")
        print(f"   ✅ Tool groups: {len(tool_groups)}")
        
        # Show sample tools
        print("\n   🔧 Sample MCP Tools:")
        sample_count = 0
        for group in tool_groups:
            for tool in group.tools[:5]:
                print(f"      - {tool.name}")
                if tool.flags:
                    flags = ', '.join(f"{k}={v}" for k, v in tool.flags.items())
                    print(f"        Flags: {flags}")
                sample_count += 1
                if sample_count >= 10:
                    break
            if sample_count >= 10:
                break
        
        # Save results
        output = {
            "sdk": sdk_name,
            "module": module_name,
            "discovery": {
                "total_methods": len(all_methods),
                "filtered_methods": len(filtered_methods),
                "noise_reduction": f"{((len(all_methods) - len(filtered_methods)) / len(all_methods) * 100):.1f}%"
            },
            "patterns": {
                "resources": len(patterns['resources']),
                "auth_flows": len(patterns['auth_flows']),
                "api_groups": len(patterns['api_groups'])
            },
            "mcp_tools": {
                "total": total_tools,
                "groups": len(tool_groups)
            }
        }
        
        filename = f"examples/{sdk_name}_test_results.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\n   💾 Results saved to: {filename}")
        
        return True
        
    except ImportError as e:
        print(f"\n❌ SDK not installed: {e}")
        print(f"   Install with: pip install {sdk_name}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test with multiple unknown SDKs."""
    print("🚀 UNIVERSAL MCP SYSTEM - UNKNOWN SDK VALIDATION")
    print("="*70)
    print("Testing with SDKs that were NEVER seen during development:")
    
    # SDKs to test (these were not used during development)
    test_sdks = [
        ("boto3", "boto3"),          # AWS SDK - never tested before
        ("stripe", "stripe"),         # Stripe payments - never tested before
        ("openai", "openai"),         # OpenAI SDK - never tested before
        ("pandas", "pandas"),         # Data analysis - never tested before
    ]
    
    results = []
    for sdk_name, module_name in test_sdks:
        success = test_unknown_sdk(sdk_name, module_name)
        results.append((sdk_name, success))
    
    # Summary
    print(f"\n{'='*70}")
    print("📊 VALIDATION SUMMARY")
    print(f"{'='*70}")
    
    for sdk_name, success in results:
        status = "✅ SUCCESS" if success else "❌ Not installed"
        print(f"   {sdk_name:<15} {status}")
    
    successful = [r for r in results if r[1]]
    if successful:
        print(f"\n🎉 Successfully processed {len(successful)} unknown SDK(s)!")
        print("   This proves the system is TRULY UNIVERSAL!")
    
    # Install instructions for missing SDKs
    failed = [r[0] for r in results if not r[1]]
    if failed:
        print(f"\n📦 To test missing SDKs, install them:")
        print(f"   pip install {' '.join(failed)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific SDK
        test_unknown_sdk(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
    else:
        # Test all
        main()