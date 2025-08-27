#!/usr/bin/env python3
"""
Universal MCP Server

A fully universal MCP server that auto-generates tools from ANY Python SDK.
No SDK-specific code required - works with GitHub, Kubernetes, Azure, and any other SDK.
"""

import asyncio
import json
import sys
import logging
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

logger = logging.getLogger(__name__)

from introspector_v2 import UniversalIntrospector
from mcp_tool_generator import UniversalMCPToolGenerator, MCPToolGroup
from mcp_execution_bridge import MCPExecutionBridge

class UniversalMCPServer:
    """
    Universal MCP server that works with ANY Python SDK.
    """
    
    def __init__(self, sdk_name: str, module_name: str):
        """
        Initialize the universal MCP server.
        
        Args:
            sdk_name: Name of the SDK (e.g., 'github', 'kubernetes')
            module_name: Module to introspect (e.g., 'github', 'kubernetes.client')
        """
        self.sdk_name = sdk_name
        self.module_name = module_name
        self.server = Server(f"universal-{sdk_name}-server")
        self.tool_groups = []
        self.tool_map = {}  # Map tool names to their metadata
        self.execution_bridge = MCPExecutionBridge(sdk_name, module_name)
        
        # Setup server handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Setup MCP server handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List all available tools."""
            tools = []
            
            for group in self.tool_groups:
                for tool in group.tools:
                    # Create MCP Tool object
                    mcp_tool = Tool(
                        name=tool.name,
                        description=tool.description,
                        inputSchema=tool.input_schema
                    )
                    tools.append(mcp_tool)
            
            return tools
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]):
            """Execute a tool."""
            
            # Find the tool metadata
            if name not in self.tool_map:
                # Return list of content items directly
                return [
                    {"type": "text", "text": json.dumps({"error": f"Tool '{name}' not found"})}
                ]
            
            tool_metadata = self.tool_map[name]
            
            # Check for destructive flag
            if tool_metadata.flags.get('destructive') and tool_metadata.flags.get('confirm'):
                # In production, this would require user confirmation
                # For now, we'll add a warning to the result
                pass
            
            # Execute the tool
            try:
                result = await self.execution_bridge.execute_tool(
                    tool_name=name,
                    sdk_method=tool_metadata.sdk_method,
                    arguments=arguments
                )
                
                # Debug logging
                logger.info(f"🔍 Tool execution result type: {type(result)}")
                logger.info(f"🔍 Tool execution result: {result}")
                
                # Ensure result is JSON serializable
                if not isinstance(result, (dict, list, str, int, float, bool, type(None))):
                    logger.warning(f"⚠️ Non-JSON result type: {type(result)}, converting to string")
                    result = {"status": "success", "result": str(result)}
                
                # Format the result - return list of content items directly
                formatted_result = [
                    {"type": "text", "text": json.dumps(result, indent=2)}
                ]
                
                logger.info(f"🔍 Result formatted successfully")
                return formatted_result
                
            except Exception as e:
                # Return list of content items directly
                return [
                    {"type": "text", "text": json.dumps({"error": str(e), "tool": name})}
                ]
    
    async def initialize(self, max_tools: int = 100):
        """
        Initialize the server by discovering and generating tools.
        
        Args:
            max_tools: Maximum number of tools to generate (to avoid overwhelming the LLM)
        """
        print(f"🚀 Initializing Universal MCP Server for {self.sdk_name}")
        print(f"📦 Module: {self.module_name}")
        
        # Step 1: Introspect the SDK
        print("🔍 Discovering SDK methods...")
        introspector = UniversalIntrospector(sdk_name=self.sdk_name)
        all_methods = introspector.discover_from_module(self.module_name)
        filtered_methods = introspector.filter_high_value_methods(all_methods)
        
        print(f"   Found {len(all_methods)} methods → {len(filtered_methods)} high-value")
        
        # Limit methods if needed
        if len(filtered_methods) > max_tools:
            print(f"   Limiting to top {max_tools} methods")
            filtered_methods = filtered_methods[:max_tools]
        
        # Step 2: Generate MCP tools
        print("🔧 Generating MCP tools...")
        generator = UniversalMCPToolGenerator(self.sdk_name)
        self.tool_groups = generator.generate_tools(filtered_methods)
        
        # Build tool map for quick lookup
        for group in self.tool_groups:
            for tool in group.tools:
                self.tool_map[tool.name] = tool
        
        total_tools = sum(len(g.tools) for g in self.tool_groups)
        print(f"   Generated {total_tools} MCP tools in {len(self.tool_groups)} groups")
        
        # Show some sample tools
        print("\n📋 Sample tools:")
        sample_count = 0
        for group in self.tool_groups:
            for tool in group.tools[:3]:
                print(f"   • {tool.name}")
                if tool.flags:
                    flags = ', '.join(f"{k}={v}" for k, v in tool.flags.items())
                    print(f"     Flags: {flags}")
                sample_count += 1
                if sample_count >= 5:
                    break
            if sample_count >= 5:
                break
        
        print(f"\n✅ Server initialized successfully!")
        print(f"   {total_tools} tools ready for MCP Inspector")
    
    async def run(self):
        """Run the MCP server."""
        print(f"\n🌐 Starting Universal MCP Server for {self.sdk_name}")
        print("   Connect with MCP Inspector to test the tools")
        print("   Press Ctrl+C to stop")
        
        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point."""
    # Parse command line arguments
    if len(sys.argv) < 3:
        print("Usage: python universal_mcp_server.py <sdk_name> <module_name> [max_tools]")
        print("\nExamples:")
        print("  python universal_mcp_server.py github github")
        print("  python universal_mcp_server.py requests requests")
        print("  python universal_mcp_server.py kubernetes kubernetes 50")
        print("  python universal_mcp_server.py azure_storage azure.storage.blob")
        sys.exit(1)
    
    sdk_name = sys.argv[1]
    module_name = sys.argv[2]
    max_tools = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    
    # Create and initialize server
    server = UniversalMCPServer(sdk_name, module_name)
    await server.initialize(max_tools)
    
    # Run the server
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())