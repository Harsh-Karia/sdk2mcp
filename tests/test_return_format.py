#!/usr/bin/env python3
"""
Test different return formats to identify the correct one.
"""

import json
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

def create_test_server():
    """Create test server with different return formats."""
    server = Server("test-format")
    
    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="test_format1",
                description="Test format 1: dict with content key",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="test_format2", 
                description="Test format 2: list directly",
                inputSchema={"type": "object", "properties": {}}
            ),
            Tool(
                name="test_format3",
                description="Test format 3: dict without isError",
                inputSchema={"type": "object", "properties": {}}
            )
        ]
    
    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        print(f"DEBUG: Tool called: {name}", flush=True)
        
        if name == "test_format1":
            # Format 1: Dictionary with content key (what we currently have)
            return {
                "content": [
                    {"type": "text", "text": json.dumps({"result": "format1"})}
                ]
            }
        
        elif name == "test_format2":
            # Format 2: Return list directly (Claude's suggestion)
            return [
                {"type": "text", "text": json.dumps({"result": "format2"})}
            ]
        
        elif name == "test_format3":
            # Format 3: Simple dict without isError
            return {
                "content": [
                    {"type": "text", "text": json.dumps({"result": "format3"})}
                ]
            }
        
        return {
            "content": [
                {"type": "text", "text": json.dumps({"error": "Unknown tool"})}
            ],
            "isError": True
        }
    
    return server

async def main():
    print("Starting test server for format debugging...")
    server = create_test_server()
    
    async with stdio_server() as streams:
        await server.run(
            streams[0],
            streams[1], 
            server.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())