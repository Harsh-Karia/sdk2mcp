#!/usr/bin/env python3
"""
Test script for brand new SDK - Markdown
Shows verifiable results with the Universal MCP system.
"""

from introspector_v2 import UniversalIntrospector
from mcp_tool_generator import UniversalMCPToolGenerator
import markdown

# Test 1: Discover methods
print("🔍 Testing Python-Markdown SDK Discovery")
print("=" * 50)

introspector = UniversalIntrospector('markdown')
methods = introspector.discover_from_module('markdown')
filtered = introspector.filter_high_value_methods(methods)

print(f"✅ Discovered: {len(methods)} methods")
print(f"✅ After filtering: {len(filtered)} high-value methods")

# Show some interesting methods
print("\n📋 Sample Methods Found:")
for method in filtered[:10]:
    print(f"   • {method.name}: {method.full_name}")

# Test 2: Generate MCP tools
print("\n🔧 Generating MCP Tools")
print("-" * 50)

generator = UniversalMCPToolGenerator('markdown')
tool_groups = generator.generate_tools(filtered[:10])

print(f"✅ Generated {sum(len(g.tools) for g in tool_groups)} MCP tools")

# Test 3: Direct verification
print("\n🧪 Direct Verification Test")
print("-" * 50)

test_markdown = """
# Hello World
This is **bold** and this is *italic*.

- Item 1
- Item 2

[Link to GitHub](https://github.com)
"""

md = markdown.Markdown()
html_output = md.convert(test_markdown)

print("Input Markdown:")
print(test_markdown)
print("\nExpected HTML Output:")
print(html_output)
print("\n✅ This is what the MCP tools should produce!")
print("\n📝 To test in MCP Inspector:")
print("1. Start: python3 universal_mcp_server.py markdown markdown 20")
print("2. Look for tool: markdown_convert or markdown_markdown")  
print("3. Test with input: {'text': '# Hello World'}")
print("4. Verify you get HTML output: <h1>Hello World</h1>")