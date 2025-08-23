#!/usr/bin/env python3
"""
Test the Universal MCP Server initialization
"""

import asyncio
from universal_mcp_server import UniversalMCPServer

async def test_server():
    """Test server initialization."""
    print("🧪 Testing Universal MCP Server")
    print("="*60)
    
    # Test with requests SDK (small and simple)
    server = UniversalMCPServer("requests", "requests")
    await server.initialize(max_tools=20)
    
    # List the tools
    print("\n📋 Available tools:")
    tools = await server.server.list_tools()
    
    for i, tool in enumerate(tools[:10], 1):
        print(f"{i:2}. {tool.name}")
        print(f"    {tool.description[:80]}...")
        if hasattr(tool, 'inputSchema'):
            required = tool.inputSchema.get('required', [])
            if required:
                print(f"    Required params: {', '.join(required)}")
    
    print(f"\n✅ Server test complete! {len(tools)} tools available")

if __name__ == "__main__":
    asyncio.run(test_server())