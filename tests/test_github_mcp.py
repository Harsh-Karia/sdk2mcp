#!/usr/bin/env python3
"""
Test GitHub SDK with MCP server to ensure everything works.
"""

import asyncio
import json
from universal_mcp_server import UniversalMCPServer

async def test_github_mcp():
    """Test GitHub SDK through MCP server."""
    
    print("🧪 Testing GitHub SDK with MCP Server")
    print("=" * 50)
    
    # Initialize server
    server = UniversalMCPServer("github", "github")
    await server.initialize(max_tools=20)
    
    # Get list of tools
    list_tools_handler = None
    call_tool_handler = None
    
    for handler_name, handler in server.server._handlers.items():
        if "tools/list" in handler_name:
            list_tools_handler = handler
        elif "tools/call" in handler_name:
            call_tool_handler = handler
    
    if list_tools_handler:
        tools = await list_tools_handler.function()
        print(f"✅ Found {len(tools)} GitHub tools")
        
        # Show some tool names
        print("\n📋 Sample GitHub tools:")
        for tool in tools[:10]:
            print(f"   • {tool.name}: {tool.description[:60]}...")
        
        # Find a safe read-only tool to test
        test_tool = None
        for tool in tools:
            if "get_user" in tool.name.lower() or "search" in tool.name.lower():
                test_tool = tool
                break
        
        if test_tool and call_tool_handler:
            print(f"\n🔍 Testing tool: {test_tool.name}")
            print(f"   Description: {test_tool.description}")
            
            # Test with a safe public query
            test_args = {}
            if "search" in test_tool.name.lower():
                test_args = {"q": "python", "sort": "stars", "per_page": 1}
            elif "get_user" in test_tool.name.lower():
                test_args = {"login": "octocat"}  # GitHub's mascot user
            
            try:
                print(f"   Arguments: {test_args}")
                result = await call_tool_handler.function(test_tool.name, test_args)
                
                print(f"\n📊 Result structure:")
                print(f"   Type: {type(result)}")
                
                if isinstance(result, list):
                    print(f"   ✅ Result is a list (correct format)")
                    if len(result) > 0:
                        first_item = result[0]
                        if isinstance(first_item, dict):
                            print(f"   ✅ First item is a dict")
                            if "type" in first_item and "text" in first_item:
                                print(f"   ✅ Has 'type' and 'text' fields")
                                
                                # Parse the text content
                                try:
                                    text_data = json.loads(first_item['text'])
                                    print(f"\n📦 Response data keys: {list(text_data.keys())[:5]}")
                                    
                                    if "error" in text_data:
                                        print(f"   ⚠️ Error: {text_data['error']}")
                                    else:
                                        print(f"   ✅ Tool execution successful!")
                                        
                                        # Show a sample of the result
                                        result_str = json.dumps(text_data, indent=2)
                                        if len(result_str) > 500:
                                            result_str = result_str[:500] + "..."
                                        print(f"\n📄 Sample result:\n{result_str}")
                                        
                                except json.JSONDecodeError as e:
                                    print(f"   ❌ Could not parse JSON: {e}")
                            else:
                                print(f"   ❌ Missing required fields")
                        else:
                            print(f"   ❌ First item is not a dict: {type(first_item)}")
                else:
                    print(f"   ❌ Result is not a list: {result}")
                    
            except Exception as e:
                print(f"   ❌ Tool execution failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("   ⚠️ No suitable test tool found")
    
    print("\n✅ GitHub MCP test complete!")

if __name__ == "__main__":
    asyncio.run(test_github_mcp())