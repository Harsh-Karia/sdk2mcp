#!/usr/bin/env python3
"""
Test MCP server with HTTP transport to bypass stdio issues.
"""

import asyncio
import json
import base64
import uvicorn
from mcp.server import Server
from mcp.server.fastapi import FastAPIServerTransport
from mcp.types import TextContent, Tool, CallToolResult

def create_http_server():
    """Create MCP server with HTTP transport."""
    server = Server("test-http")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        print("🔍 HTTP: list_tools called")
        return [
            Tool(
                name="http_b64encode",
                description="HTTP Base64 encoding test", 
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
        print(f"🔍 HTTP: call_tool - {name}, {arguments}")
        
        if name == "http_b64encode":
            s = arguments.get("s", "")
            encoded = base64.b64encode(s.encode()).decode()
            
            result = {
                "status": "success",
                "input": s, 
                "encoded": encoded,
                "transport": "http"
            }
            
            print(f"🔍 HTTP: Returning {result}")
            
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
    print("🚀 Starting MCP server with HTTP transport on port 8000...")
    print("🔗 Connect MCP Inspector to: http://localhost:8000/mcp")
    
    server = create_http_server()
    transport = FastAPIServerTransport("/mcp")
    
    app = transport.create_app(server)
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server_instance = uvicorn.Server(config)
    
    await server_instance.serve()

if __name__ == "__main__":
    asyncio.run(main())