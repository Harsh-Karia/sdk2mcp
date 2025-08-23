#!/usr/bin/env python3
"""
Example usage of the Universal SDK-to-MCP Converter.

This demonstrates how to use the system with different SDKs.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from introspector_v2 import UniversalIntrospector
from mcp_tool_generator import UniversalMCPToolGenerator
from pattern_recognizer import UniversalPatternRecognizer

def example_basic_usage():
    """Basic example of SDK introspection and tool generation."""
    
    # Step 1: Introspect any SDK
    introspector = UniversalIntrospector('requests')
    methods = introspector.discover_from_module('requests')
    filtered = introspector.filter_high_value_methods(methods)
    
    print(f"Discovered {len(methods)} methods, filtered to {len(filtered)}")
    
    # Step 2: Generate MCP tools
    generator = UniversalMCPToolGenerator('requests')
    tool_groups = generator.generate_tools(filtered)
    
    print(f"Generated {len(tool_groups)} tool groups")
    
    return tool_groups

def example_with_pattern_analysis():
    """Example showing pattern recognition."""
    
    # Introspect SDK
    introspector = UniversalIntrospector('json')
    methods = introspector.discover_from_module('json')
    
    # Analyze patterns
    recognizer = UniversalPatternRecognizer()
    patterns = recognizer.analyze_patterns(methods)
    
    print("Pattern Analysis Results:")
    print(f"- Resources found: {len(patterns.get('resources', []))}")
    print(f"- CRUD operations: {len(patterns.get('crud_operations', []))}")
    print(f"- Auth flows: {len(patterns.get('auth_flows', []))}")
    print(f"- API groups: {len(patterns.get('api_groups', []))}")
    
    return patterns

if __name__ == "__main__":
    print("🚀 Universal SDK-to-MCP Converter Examples")
    print("=" * 50)
    
    # Run examples
    print("\n📦 Basic Usage Example:")
    example_basic_usage()
    
    print("\n🔍 Pattern Analysis Example:")
    example_with_pattern_analysis()
    
    print("\n✅ Examples completed!")