#!/usr/bin/env python3
"""
SDK2MCP Server - Phase 1
A minimal MCP server with one hardcoded tool to test the foundation.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# Initialize the MCP server
app = Server("sdk2mcp")


# Define our test tool - a simple hardcoded tool that lists mock SDK methods
@app.list_tools()
async def list_tools() -> List[Tool]:
    """
    List available tools. For Phase 1, we have one hardcoded test tool.
    """
    return [
        Tool(
            name="list_sdk_methods",
            description="List available methods for a given SDK (returns mock data for now)",
            inputSchema={
                "type": "object",
                "properties": {
                    "sdk_name": {
                        "type": "string",
                        "description": "Name of the SDK to list methods for (e.g., 'github', 'kubernetes', 'azure')"
                    },
                    "category": {
                        "type": "string",
                        "description": "Optional category to filter methods (e.g., 'repos', 'issues', 'pulls')",
                        "default": None
                    }
                },
                "required": ["sdk_name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """
    Handle tool calls. For Phase 1, we handle our single test tool.
    """
    if name == "list_sdk_methods":
        sdk_name = arguments.get("sdk_name", "unknown")
        category = arguments.get("category")
        
        # Mock data for demonstration - in later phases this will use real introspection
        mock_methods = {
            "github": {
                "repos": ["list_repos", "get_repo", "create_repo", "delete_repo"],
                "issues": ["list_issues", "get_issue", "create_issue", "update_issue", "close_issue"],
                "pulls": ["list_pulls", "get_pull", "create_pull", "merge_pull"]
            },
            "kubernetes": {
                "pods": ["list_pods", "get_pod", "create_pod", "delete_pod", "get_pod_logs"],
                "services": ["list_services", "get_service", "create_service", "update_service"],
                "deployments": ["list_deployments", "get_deployment", "create_deployment", "scale_deployment"]
            },
            "azure": {
                "storage": ["list_storage_accounts", "create_storage_account", "delete_storage_account"],
                "compute": ["list_vms", "create_vm", "start_vm", "stop_vm", "delete_vm"],
                "network": ["list_vnets", "create_vnet", "list_subnets", "create_subnet"]
            }
        }
        
        sdk_methods = mock_methods.get(sdk_name.lower(), {})
        
        if category and category in sdk_methods:
            methods = sdk_methods[category]
            result = f"Methods for {sdk_name}.{category}:\n"
            result += "\n".join(f"  - {method}" for method in methods)
        elif sdk_methods:
            result = f"Available categories for {sdk_name}:\n"
            for cat, methods in sdk_methods.items():
                result += f"\n{cat}:\n"
                result += "\n".join(f"  - {method}" for method in methods[:3])
                if len(methods) > 3:
                    result += f"\n  ... and {len(methods) - 3} more"
        else:
            result = f"SDK '{sdk_name}' not found. Available SDKs: github, kubernetes, azure"
        
        return [TextContent(type="text", text=result)]
    
    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """
    Main entry point for the MCP server.
    Uses stdio transport for MCP Inspector compatibility.
    """
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())