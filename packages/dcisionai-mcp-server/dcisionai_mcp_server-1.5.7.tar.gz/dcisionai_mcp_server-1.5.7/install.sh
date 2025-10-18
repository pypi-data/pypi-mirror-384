#!/bin/bash

# DcisionAI MCP Server Configuration Script
# This script configures the DcisionAI MCP Server for Cursor (no installation needed!)

echo "🚀 Configuring DcisionAI MCP Server for Cursor..."

# Check if uvx is available
if ! command -v uvx &> /dev/null; then
    echo "❌ uvx is not installed. Please install uv first:"
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uvx is available - no local installation needed!"

# Create Cursor MCP configuration directory if it doesn't exist
CURSOR_MCP_DIR="$HOME/.cursor"
if [ ! -d "$CURSOR_MCP_DIR" ]; then
    echo "📁 Creating Cursor MCP configuration directory..."
    mkdir -p "$CURSOR_MCP_DIR"
fi

# Create or update mcp.json
MCP_CONFIG="$CURSOR_MCP_DIR/mcp.json"
echo "⚙️  Configuring Cursor MCP settings..."

# Check if mcp.json already exists
if [ -f "$MCP_CONFIG" ]; then
    echo "📝 Found existing mcp.json. Creating backup..."
    cp "$MCP_CONFIG" "$MCP_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Create the configuration
cat > "$MCP_CONFIG" << 'EOF'
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
EOF

echo "✅ Configuration created at $MCP_CONFIG"

# Test the configuration
echo "🧪 Testing configuration..."
uvx dcisionai-mcp-server@latest --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Configuration test passed!"
else
    echo "⚠️  Configuration test failed. Please check your uv installation."
fi

echo ""
echo "🎉 Configuration complete!"
echo ""
echo "📋 Next steps:"
echo "1. Restart Cursor IDE"
echo "2. Go to Settings → Tools & MCP"
echo "3. Verify 'dcisionai-mcp-server' is enabled with 6 tools"
echo ""
echo "💡 Usage examples:"
echo "• 'Help me optimize a production planning problem'"
echo "• 'I need to solve a portfolio optimization problem'"
echo "• 'Show me available manufacturing workflows'"
echo ""
echo "✨ No local installation needed - uvx handles everything automatically!"
echo "📚 For more information, visit: https://pypi.org/project/dcisionai-mcp-server/"
