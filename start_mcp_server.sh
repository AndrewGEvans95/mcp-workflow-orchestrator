#!/bin/bash

# Start MCP Workflow Orchestrator Server
# This script sets up the environment and starts the MCP server

cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import orchestrator, workflow_policies, audit_monitor" 2>/dev/null; then
    echo "Error: Dependencies not installed. Please run: pip install -r requirements.txt"
    exit 1
fi

# Start the MCP server
echo "Starting MCP Workflow Orchestrator Server..."
echo "Server is ready to accept connections from Claude Desktop"
echo "To stop the server, use Ctrl+C"
echo "========================================="

exec python mcp_server.py