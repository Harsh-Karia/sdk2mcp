#!/usr/bin/env python3
"""
Simple MCP server test to isolate CallToolResult issue.
"""

import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, CallToolResult

def create_simple_server():
    """Create a simple MCP server with one hardcoded tool."""
    server = Server("test-simple")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        """List available tools."""
        return [
            Tool(
                name="test_encode",
                description="Test base64 encoding",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "Text to encode"
                        }
                    },
                    "required": ["text"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> CallToolResult:
        """Execute a tool."""
        if name == "test_encode":
            # Simple hardcoded response - no execution bridge
            import base64
            text = arguments.get("text", "")
            encoded = base64.b64encode(text.encode()).decode()
            
            result = {
                "status": "success",
                "input": text,
                "output": encoded
            }
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            )
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text", 
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]
            )
    
    return server

async def main():
    """Run the simple test server."""
    server = create_simple_server()
    
    async with stdio_server() as streams:
        await server.run(
            streams[0], 
            streams[1], 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())