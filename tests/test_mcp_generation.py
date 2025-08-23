#!/usr/bin/env python3
"""
Test MCP tool generation for all SDKs
"""

from introspector_v2 import UniversalIntrospector
from mcp_tool_generator import UniversalMCPToolGenerator
import json

def test_sdk_tool_generation(sdk_name: str, module_name: str):
    """Test MCP tool generation for a specific SDK."""
    print(f"\n{'='*60}")
    print(f"🔧 GENERATING MCP TOOLS: {sdk_name}")
    print(f"{'='*60}")
    
    # Step 1: Introspect
    introspector = UniversalIntrospector(sdk_name=sdk_name)
    all_methods = introspector.discover_from_module(module_name)
    filtered_methods = introspector.filter_high_value_methods(all_methods)
    
    print(f"📊 Methods: {len(all_methods)} discovered → {len(filtered_methods)} filtered")
    
    # Step 2: Generate MCP tools
    generator = UniversalMCPToolGenerator(sdk_name)
    tool_groups = generator.generate_tools(filtered_methods)
    
    print(f"🔧 Generated {len(tool_groups)} tool groups")
    
    # Show tool groups
    total_tools = 0
    for group in tool_groups:
        print(f"\n📦 {group.name}:")
        print(f"   {len(group.tools)} tools")
        
        # Show sample tools
        for tool in group.tools[:3]:
            print(f"   • {tool.name}")
            if tool.flags:
                flags_str = ', '.join(f"{k}={v}" for k, v in tool.flags.items())
                print(f"     Flags: {flags_str}")
        
        if len(group.tools) > 3:
            print(f"   ... and {len(group.tools) - 3} more")
        
        total_tools += len(group.tools)
    
    print(f"\n📊 Total MCP tools generated: {total_tools}")
    
    # Export to JSON for review
    output_file = f"{sdk_name}_mcp_tools.json"
    generator.export_to_json(tool_groups, output_file)
    print(f"💾 Exported to: {output_file}")
    
    return tool_groups

def main():
    """Test MCP tool generation for all SDKs."""
    print("🚀 TESTING MCP TOOL GENERATION")
    print("="*60)
    
    sdks = [
        ("github", "github"),
        ("requests", "requests"),
        ("kubernetes", "kubernetes"),
        ("azure_mgmt_resource", "azure.mgmt.resource"),
        ("azure_storage_blob", "azure.storage.blob")
    ]
    
    results = {}
    for sdk_name, module_name in sdks:
        try:
            tool_groups = test_sdk_tool_generation(sdk_name, module_name)
            results[sdk_name] = {
                'groups': len(tool_groups),
                'total_tools': sum(len(g.tools) for g in tool_groups)
            }
        except Exception as e:
            print(f"❌ Error with {sdk_name}: {e}")
            results[sdk_name] = {'error': str(e)}
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 MCP TOOL GENERATION SUMMARY")
    print(f"{'='*60}")
    
    print(f"\n{'SDK':<25} {'Groups':<10} {'Tools':<10}")
    print("-" * 45)
    for sdk_name, result in results.items():
        if 'error' not in result:
            print(f"{sdk_name:<25} {result['groups']:<10} {result['total_tools']:<10}")
        else:
            print(f"{sdk_name:<25} ERROR")
    
    print("\n✅ MCP tool generation complete!")
    print("   Tools are ready to be exposed via MCP server")

if __name__ == "__main__":
    main()