#!/usr/bin/env python3
"""
Debug MCP CallToolResult format issue.
"""

import json
from mcp.types import TextContent, CallToolResult

def test_call_tool_result():
    """Test proper CallToolResult creation."""
    
    print("🔍 Testing CallToolResult format...")
    
    # Test 1: Simple success result
    try:
        result = CallToolResult(
            content=[TextContent(
                type="text", 
                text=json.dumps({"result": "SGVsbG8gV29ybGQ="}, indent=2)
            )]
        )
        print("✅ Simple CallToolResult created successfully")
        print(f"   Content: {result.content}")
        
    except Exception as e:
        print(f"❌ Simple CallToolResult failed: {e}")
    
    # Test 2: Error result format
    try:
        error_result = CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps({
                    "error": "Test error message",
                    "tool": "test_tool"
                })
            )]
        )
        print("✅ Error CallToolResult created successfully")
        
    except Exception as e:
        print(f"❌ Error CallToolResult failed: {e}")
    
    # Test 3: What might be causing the tuple error?
    print("\n🔍 Investigating tuple error...")
    
    # Check if we're accidentally creating tuples somewhere
    test_data = {
        "status": "success",
        "tool": "base64_b64encode", 
        "result": "SGVsbG8gV29ybGQ="
    }
    
    formatted_result = CallToolResult(
        content=[TextContent(
            type="text",
            text=json.dumps(test_data, indent=2)
        )]
    )
    print("✅ Real-world format test passed")

if __name__ == "__main__":
    test_call_tool_result()