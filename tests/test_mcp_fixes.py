#!/usr/bin/env python3
"""
Test the MCP validation fixes.
"""

import asyncio
import json
from universal_mcp_server import UniversalMCPServer

async def test_mcp_fixes():
    """Test that the MCP server returns proper dictionary format."""
    
    print("🧪 Testing MCP Validation Fixes")
    print("=" * 40)
    
    # Initialize server
    server = UniversalMCPServer("base64", "base64")
    await server.initialize(max_tools=5)
    
    # Get the call_tool handler directly
    tools = await server.server.list_tools()()
    print(f"✅ Listed {len(tools)} tools successfully")
    
    # Find a base64 tool
    b64encode_tool = None
    for tool in tools:
        if "b64encode" in tool.name:
            b64encode_tool = tool
            break
    
    if not b64encode_tool:
        print("❌ No b64encode tool found")
        return
    
    print(f"🔍 Testing tool: {b64encode_tool.name}")
    
    # Test the call_tool handler directly
    call_tool_handler = None
    for handler_name, handler in server.server._handlers.items():
        if "tools/call" in handler_name:
            call_tool_handler = handler
            break
    
    if not call_tool_handler:
        print("❌ call_tool handler not found")
        return
    
    # Test with string input (should be converted to bytes)
    test_args = {"s": "Hello World!"}
    
    try:
        result = await call_tool_handler.function(b64encode_tool.name, test_args)
        
        print(f"🔍 Result type: {type(result)}")
        print(f"🔍 Result structure: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            if "content" in result:
                content = result["content"]
                if isinstance(content, list) and len(content) > 0:
                    first_content = content[0]
                    if isinstance(first_content, dict) and "type" in first_content and "text" in first_content:
                        print("✅ Result format is correct!")
                        print(f"🎯 Content type: {first_content['type']}")
                        
                        # Parse the text content
                        try:
                            text_data = json.loads(first_content['text'])
                            print(f"🎯 Text data: {text_data}")
                            
                            if "result" in text_data:
                                print(f"🎯 Base64 result: {text_data['result']}")
                                print("✅ Base64 encoding worked!")
                            
                        except json.JSONDecodeError:
                            print("⚠️ Text content is not JSON")
                    else:
                        print("❌ Content item format incorrect")
                else:
                    print("❌ Content array empty or invalid")
            else:
                print("❌ No 'content' key in result")
        else:
            print("❌ Result is not a dictionary")
        
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 MCP fix validation complete!")

if __name__ == "__main__":
    asyncio.run(test_mcp_fixes())