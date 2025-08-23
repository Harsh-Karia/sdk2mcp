#!/usr/bin/env python3
"""
Completely isolated MCP server test to identify tuple issue source.
"""

import asyncio
import json
import base64
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool, CallToolResult

def create_isolated_server():
    """Create minimal MCP server with hardcoded base64 tool."""
    server = Server("debug-isolated")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="debug_base64_encode",
                description="Debug base64 encoding",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to encode"}
                    },
                    "required": ["text"]
                }
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> CallToolResult:
        print(f"🔍 DEBUG: Tool called: {name}")
        print(f"🔍 DEBUG: Arguments: {arguments}")
        
        if name == "debug_base64_encode":
            try:
                # Direct base64 encoding - no execution bridge
                text = arguments.get("text", "")
                encoded = base64.b64encode(text.encode()).decode()
                
                result_data = {
                    "status": "success",
                    "input": text,
                    "output": encoded,
                    "tool": name
                }
                
                print(f"🔍 DEBUG: Result data: {result_data}")
                print(f"🔍 DEBUG: Creating TextContent...")
                
                text_content = TextContent(
                    type="text",
                    text=json.dumps(result_data, indent=2)
                )
                
                print(f"🔍 DEBUG: TextContent created: {text_content}")
                print(f"🔍 DEBUG: Creating CallToolResult...")
                
                call_result = CallToolResult(content=[text_content])
                
                print(f"🔍 DEBUG: CallToolResult created successfully")
                print(f"🔍 DEBUG: CallToolResult content: {call_result.content}")
                
                return call_result
                
            except Exception as e:
                print(f"❌ DEBUG: Exception in tool execution: {e}")
                import traceback
                traceback.print_exc()
                
                error_content = TextContent(
                    type="text",
                    text=json.dumps({"error": str(e), "tool": name})
                )
                
                return CallToolResult(content=[error_content])
        
        else:
            return CallToolResult(
                content=[TextContent(
                    type="text",
                    text=json.dumps({"error": f"Unknown tool: {name}"})
                )]
            )
    
    return server

async def main():
    print("🔍 Starting isolated debug MCP server...")
    server = create_isolated_server()
    
    async with stdio_server() as streams:
        await server.run(
            streams[0], 
            streams[1], 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())