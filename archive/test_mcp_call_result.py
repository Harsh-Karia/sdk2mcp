#!/usr/bin/env python3
"""
Test CallToolResult construction to identify tuple issue.
"""

import json
from mcp.types import TextContent, CallToolResult

def test_call_result_formats():
    """Test different ways CallToolResult might be constructed incorrectly."""
    
    print("🔍 Testing CallToolResult construction patterns...")
    
    # Test data that might cause the issue
    sample_result = {
        "status": "success",
        "tool": "base64_b64encode", 
        "result": "SGVsbG8gV29ybGQ="
    }
    
    # Test 1: Correct format (what we think we're doing)
    try:
        correct = CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(sample_result, indent=2)
            )]
        )
        print("✅ Correct format works")
    except Exception as e:
        print(f"❌ Correct format failed: {e}")
    
    # Test 2: What if we accidentally pass dict items?
    try:
        # This might be what's happening accidentally somewhere
        wrong1 = CallToolResult(
            content=[TextContent(**dict(sample_result.items()))]
        )
        print("❌ This shouldn't work but did")
    except Exception as e:
        print(f"✅ Dict items correctly failed: {e}")
    
    # Test 3: What if we pass the wrong structure?
    try:
        # Check if we're accidentally passing tuples
        wrong2 = CallToolResult(
            content=[('meta', None), ('content', 'test'), ('isError', False)]
        )
        print("❌ Tuple format shouldn't work but did")
    except Exception as e:
        print(f"✅ Tuple format correctly failed: {e}")
    
    # Test 4: Check if it's a pydantic version issue
    try:
        # Maybe we need to be more explicit
        explicit = CallToolResult(
            content=[TextContent(
                type="text",
                text=json.dumps(sample_result),
                annotations=None
            )]
        )
        print("✅ Explicit format works")
    except Exception as e:
        print(f"❌ Explicit format failed: {e}")

if __name__ == "__main__":
    test_call_result_formats()