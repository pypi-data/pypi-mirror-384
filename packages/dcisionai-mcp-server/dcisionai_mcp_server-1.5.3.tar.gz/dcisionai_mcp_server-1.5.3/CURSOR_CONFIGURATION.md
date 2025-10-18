# DcisionAI MCP Server - Cursor Configuration

## Quick Setup

The DcisionAI MCP Server is now available on PyPI! Here's how to configure it in Cursor:

### 1. Configure Cursor

Add this to your `~/.cursor/mcp.json` (no installation required - uvx handles it automatically):

```json
{
  "mcpServers": {
    "dcisionai-mcp-server": {
      "command": "uvx",
      "args": [
        "dcisionai-mcp-server@latest"
      ],
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": [
        "classify_intent",
        "analyze_data",
        "build_model",
        "solve_optimization",
        "get_workflow_templates",
        "execute_workflow"
      ]
    }
  }
}
```

### 2. Restart Cursor

After updating the configuration, restart Cursor to load the MCP server.

### 3. Verify Installation

In Cursor, go to Settings → Tools & MCP and verify that:
- ✅ `dcisionai-mcp-server` shows as enabled
- ✅ 6 tools are listed
- ✅ Server status is green

## Available Tools

1. **`classify_intent`** - Classify optimization problem types
2. **`analyze_data`** - Analyze and preprocess optimization data
3. **`build_model`** - Build mathematical models with Qwen 30B
4. **`solve_optimization`** - Solve using real OR-Tools optimization
5. **`get_workflow_templates`** - Get industry workflow templates
6. **`execute_workflow`** - Execute complete optimization workflows

## Usage Examples

Ask Cursor things like:
- "Help me optimize a production planning problem with 3 products and 2 machines"
- "I need to solve a portfolio optimization problem with 5 stocks"
- "Show me available manufacturing optimization workflows"
- "Optimize my supply chain for 10 warehouses and 50 customers"

## Environment Variables (Optional)

Set these for AWS Bedrock access:
- `AWS_ACCESS_KEY_ID` - Your AWS access key
- `AWS_SECRET_ACCESS_KEY` - Your AWS secret key
- `AWS_REGION` - AWS region (default: us-east-1)

## Troubleshooting

If the server doesn't start:
1. Verify the package is installed: `pip show dcisionai-mcp-server`
2. Test the command: `dcisionai-mcp-server --help`
3. Check Cursor logs for error messages
4. Ensure Python is in your PATH

## Package Information

- **PyPI**: https://pypi.org/project/dcisionai-mcp-server/
- **Version**: 1.0.0
- **License**: MIT
- **Python**: >=3.8
