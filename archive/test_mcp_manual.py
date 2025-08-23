#!/usr/bin/env python3
"""
Manual test of MCP protocol to bypass Inspector issues.
"""

import json
import subprocess
import sys

def test_mcp_server_direct():
    """Test MCP server with direct JSON-RPC calls."""
    
    print("🧪 Testing MCP server with direct JSON-RPC...")
    
    # Start the test server
    proc = subprocess.Popen(
        [sys.executable, "test_mcp_direct.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    try:
        # Send initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"}
            }
        }
        
        print("📤 Sending initialize request...")
        proc.stdin.write(json.dumps(init_request) + "\n")
        proc.stdin.flush()
        
        # Read response
        response = proc.stdout.readline()
        print(f"📥 Initialize response: {response.strip()}")
        
        # Send tools/list request
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        print("📤 Sending tools/list request...")
        proc.stdin.write(json.dumps(list_tools_request) + "\n")
        proc.stdin.flush()
        
        # Read response
        response = proc.stdout.readline()
        print(f"📥 Tools list response: {response.strip()}")
        
        # Send tool call
        call_tool_request = {
            "jsonrpc": "2.0", 
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "test_b64encode",
                "arguments": {"s": "Hello World"}
            }
        }
        
        print("📤 Sending tools/call request...")
        proc.stdin.write(json.dumps(call_tool_request) + "\n")
        proc.stdin.flush()
        
        # Read response
        response = proc.stdout.readline()
        print(f"📥 Tool call response: {response.strip()}")
        
        # Check stderr for debug logs
        stderr_output = proc.stderr.read()
        if stderr_output:
            print(f"🔍 Server debug logs:\n{stderr_output}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_mcp_server_direct()