#!/bin/bash
# Startup script for SDK2MCP server

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "Starting SDK2MCP MCP Server..."
echo "This server uses stdio transport for MCP Inspector"
echo "Press Ctrl+C to stop"
echo "----------------------------------------"

python server.py