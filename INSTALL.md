# Installation Guide

## Prerequisites

- Python 3.9 or higher
- pip package manager
- Git (to clone the repository)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/mcpuppet.git
cd mcpuppet
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Test the Installation

```bash
python main.py status
```

You should see a system status output showing MCPuppet is ready.

## Configuration

### Basic Configuration

The system works out of the box with the default configuration in `config.json`. This includes:

- Default downstream server URLs (will fail gracefully if not available)
- Basic workflow policies
- Audit logging configuration

### Custom Configuration

To customize the system:

1. **Edit `config.json`** to modify:
   - Downstream server URLs
   - Workflow policies
   - Audit settings

2. **Review `workflow_templates.py`** to:
   - Add new workflow templates
   - Modify existing workflow sequences

## Running the System

### Standalone Mode

```bash
# Run all demos
python main.py demo

# Run specific demo
python main.py demo-success

# Interactive mode
python main.py interactive

# Check system status
python main.py status
```

### Claude Desktop Integration

See [CLAUDE_SETUP.md](CLAUDE_SETUP.md) for detailed instructions on connecting to Claude Desktop.

## Verification

After installation, verify the system works:

1. **Test basic functionality**:
   ```bash
   python main.py demo-success
   ```

2. **Check audit logs**:
   ```bash
   ls -la audit_logs/
   ```

3. **Test MCP server** (if using Claude Desktop):
   ```bash
   python mcp_server.py
   # Should wait for JSON-RPC input
   ```

## Troubleshooting

### Common Issues

**ImportError: No module named 'X'**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

**Permission denied errors**
- Check file permissions: `chmod +x *.py`
- Ensure audit_logs directory is writable

**Config file not found**
- Verify `config.json` exists in the project root
- Check file permissions

### Getting Help

1. Check the [README.md](README.md) for feature documentation
2. Review the [CLAUDE_SETUP.md](CLAUDE_SETUP.md) for Claude Desktop integration
3. Check the `audit_logs/` directory for error messages

## Next Steps

After successful installation:

1. **Explore the demos** to understand workflow orchestration
2. **Set up Claude Desktop integration** for AI-powered workflow management
3. **Customize workflow templates** for your specific use cases
4. **Configure downstream servers** for production use