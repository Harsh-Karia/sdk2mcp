#!/usr/bin/env python3
"""
Quick test script to verify the MCP server starts correctly.
This doesn't test the full MCP protocol, just that the server imports and initializes.
"""

import sys
import asyncio
from server import app, list_tools, call_tool


async def test_server():
    """Test that the server components work"""
    print("Testing SDK2MCP Server Components...")
    
    # Test 1: Check server is initialized
    print(f"✓ Server initialized: {app.name}")
    
    # Test 2: List tools
    tools = await list_tools()
    print(f"✓ Found {len(tools)} tool(s)")
    for tool in tools:
        print(f"  - {tool.name}: {tool.description[:50]}...")
    
    # Test 3: Call the test tool
    result = await call_tool("list_sdk_methods", {"sdk_name": "github"})
    print(f"✓ Tool call successful")
    print(f"  Response preview: {result[0].text[:100]}...")
    
    # Test 4: Call with category filter
    result = await call_tool("list_sdk_methods", {"sdk_name": "github", "category": "issues"})
    print(f"✓ Tool call with category successful")
    
    print("\n✅ All tests passed! Server is ready for MCP Inspector.")
    print("\nTo connect with MCP Inspector:")
    print("1. Run: python server.py")
    print("2. In MCP Inspector, connect to stdio transport")
    print("3. Point to the server.py file path")
    

if __name__ == "__main__":
    try:
        asyncio.run(test_server())
    except Exception as e:
        print(f"❌ Test failed: {e}", file=sys.stderr)
        sys.exit(1)