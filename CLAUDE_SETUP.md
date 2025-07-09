# Setting Up MCPuppet with Claude Desktop

This guide explains how to connect MCPuppet to your Claude Desktop app.

## Prerequisites

1. **Claude Desktop App**: Make sure you have Claude Desktop installed
2. **Python Environment**: Ensure the virtual environment is set up and dependencies are installed
3. **Project Path**: Update the paths in the configuration to match your system

## Step 1: Prepare the MCP Server

1. **Activate the virtual environment**:
   ```bash
   cd /path/to/your/project
   source venv/bin/activate
   ```

2. **Test the MCP server locally** (optional):
   ```bash
   python mcp_server.py
   ```
   The server will wait for JSON-RPC input via stdin.

## Step 2: Configure Claude Desktop

1. **Find your Claude Desktop configuration directory**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

2. **Update the configuration file**:
   
   If the file doesn't exist, create it. If it exists, add the MCP server configuration to the existing `mcpServers` object.

   ```json
   {
     "mcpServers": {
       "mcpuppet": {
         "command": "/path/to/your/project/venv/bin/python",
         "args": ["/path/to/your/project/mcp_server.py"]
       }
     }
   }
   ```

   **Important**: Update the path `/path/to/your/project` to match your actual project directory.

3. **Alternative: Using system Python** (not recommended):
   
   You can also use system Python, but make sure to set the PYTHONPATH:
   
   ```json
   {
     "mcpServers": {
       "mcpuppet": {
         "command": "python3",
         "args": ["/path/to/your/project/mcp_server.py"],
         "env": {
           "PYTHONPATH": "/path/to/your/project"
         }
       }
     }
   }
   ```

## Step 3: Restart Claude Desktop

1. **Quit Claude Desktop** completely
2. **Restart Claude Desktop**
3. **Check for the MCP server**: Look for the MCPuppet tools in the available tools list

## Step 4: Test the Integration

Once Claude Desktop is running with the MCP server, you can test it with prompts like:

### List Available Workflow Templates
```
Can you show me the available workflow templates?
```

### Execute a Customer Onboarding Workflow
```
Please execute the customer_onboarding workflow with session ID "test_001" and this data:
{
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "555-123-4567",
  "account_type": "premium"
}
```

### Call a Specific Tool
```
Can you call the validate_data tool with session ID "test_002" and arguments:
{
  "data": {
    "name": "Jane Smith",
    "email": "jane@example.com"
  },
  "required_fields": ["name", "email"]
}
```

### Check Workflow Status
```
What's the status of session "test_001"?
```

### Get Audit Report
```
Can you generate an audit report for session "test_001"?
```

## Available Tools

The MCP server provides these tools to Claude:

1. **`execute_workflow`**: Execute a complete workflow with a template
2. **`call_tool`**: Call a specific tool with policy enforcement
3. **`get_workflow_status`**: Get the status of a workflow session
4. **`list_templates`**: List available workflow templates
5. **`get_audit_report`**: Get comprehensive audit report

## Troubleshooting

### Server Not Starting
- Check that the virtual environment is activated
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Ensure the Python path is correct in the configuration

### Tools Not Appearing in Claude
- Make sure Claude Desktop was completely restarted
- Check the configuration file syntax (valid JSON)
- Verify the file paths are absolute and correct

### Permission Issues
- Ensure the Python script has execute permissions: `chmod +x mcp_server.py`
- Check that the virtual environment has the right permissions

### Debugging
- Check Claude Desktop logs for error messages
- Test the MCP server manually by running `python mcp_server.py` and sending JSON-RPC requests

## Example Configuration for Different Systems

### macOS (using virtual environment)
```json
{
  "mcpServers": {
    "mcpuppet": {
      "command": "/Users/YOUR_USERNAME/mcpuppet/venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/mcpuppet/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/Users/YOUR_USERNAME/mcpuppet"
      }
    }
  }
}
```

### Linux (using virtual environment)
```json
{
  "mcpServers": {
    "mcpuppet": {
      "command": "/home/YOUR_USERNAME/mcpuppet/venv/bin/python",
      "args": ["/home/YOUR_USERNAME/mcpuppet/mcp_server.py"],
      "env": {
        "PYTHONPATH": "/home/YOUR_USERNAME/mcpuppet"
      }
    }
  }
}
```

### Windows (using virtual environment)
```json
{
  "mcpServers": {
    "mcpuppet": {
      "command": "C:\\Users\\YOUR_USERNAME\\mcpuppet\\venv\\Scripts\\python.exe",
      "args": ["C:\\Users\\YOUR_USERNAME\\mcpuppet\\mcp_server.py"],
      "env": {
        "PYTHONPATH": "C:\\Users\\YOUR_USERNAME\\mcpuppet"
      }
    }
  }
}
```

## Features You Can Test

Once connected, you can:

1. **Execute workflows** with proper dependency ordering
2. **Test policy enforcement** by trying to call tools out of order
3. **Monitor workflow progress** in real-time
4. **Generate audit reports** for compliance tracking
5. **Use approval workflows** for sensitive operations

The MCP server provides a complete interface to MCPuppet, allowing Claude to interact with it as if it were any other MCP tool while maintaining all the governance and audit capabilities.