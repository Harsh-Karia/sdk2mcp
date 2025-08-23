#!/usr/bin/env python3
"""
Test MCP server with direct JSON-RPC communication to bypass Inspector issues.
"""

import asyncio
import json
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, CallToolResult
import base64

def create_test_server():
    server = Server("test-direct")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        print("🔍 DEBUG: list_tools called", file=sys.stderr)
        return [
            Tool(
                name="test_b64encode", 
                description="Test base64 encoding",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "s": {"type": "string", "description": "String to encode"}
                    },
                    "required": ["s"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> CallToolResult:
        print(f"🔍 DEBUG: call_tool invoked - name: {name}, args: {arguments}", file=sys.stderr)
        
        try:
            if name == "test_b64encode":
                s = arguments.get("s", "")
                encoded = base64.b64encode(s.encode()).decode()
                
                result = {
                    "status": "success",
                    "input": s,
                    "encoded": encoded
                }
                
                print(f"🔍 DEBUG: Returning result: {result}", file=sys.stderr)
                
                return CallToolResult(
                    content=[TextContent(
                        type="text",
                        text=json.dumps(result, indent=2)
                    )]
                )
            else:
                print(f"🔍 DEBUG: Unknown tool: {name}", file=sys.stderr)
                return CallToolResult(
                    content=[TextContent(
                        type="text", 
                        text=json.dumps({"error": f"Unknown tool: {name}"})
                    )]
                )
        except Exception as e:
            print(f"❌ DEBUG: Exception in call_tool: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({"error": str(e)})
                )]
            )
    
    return server

async def main():
    print("🚀 Starting test MCP server with stderr debug logging...", file=sys.stderr)
    server = create_test_server()
    
    async with stdio_server() as streams:
        await server.run(
            streams[0], 
            streams[1], 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())