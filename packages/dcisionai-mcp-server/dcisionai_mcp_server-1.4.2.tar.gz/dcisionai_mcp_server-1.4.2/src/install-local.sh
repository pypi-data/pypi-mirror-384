#!/bin/bash

# DcisionAI MCP Server - Local Installation Script
# This script installs the DcisionAI MCP Server locally for development and testing

set -e # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting DcisionAI MCP Server - Local Installation"
echo "====================================================="

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "📁 Project root: $PROJECT_ROOT"
echo "📁 Script directory: $SCRIPT_DIR"

# Check for Python 3.8+
echo "🐍 Checking Python version..."
PYTHON_CMD=""
if command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
elif command -v python3.9 &> /dev/null; then
    PYTHON_CMD="python3.9"
elif command -v python3.8 &> /dev/null; then
    PYTHON_CMD="python3.8"
elif command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ "$MAJOR" -gt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -ge 8 ]); then
        PYTHON_CMD="python3"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python 3.8+ not found. Please install Python 3.8 or newer."
    echo "On macOS, you can use Homebrew: brew install python@3.10"
    echo "On Ubuntu: sudo apt update && sudo apt install python3.10 python3.10-venv"
    exit 1
else
    echo "✅ Found Python: $($PYTHON_CMD --version)"
fi

# Create and activate virtual environment
echo "🔧 Setting up virtual environment..."
VENV_DIR="$PROJECT_ROOT/venv"
if [ ! -d "$VENV_DIR" ]; then
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "✅ Virtual environment created at: $VENV_DIR"
else
    echo "✅ Virtual environment already exists at: $VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
echo "✅ Virtual environment activated"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install -e "$SCRIPT_DIR"
echo "✅ DcisionAI MCP Server installed successfully"

# Set up environment variables
echo "🔧 Setting up environment variables..."
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << EOF
# DcisionAI MCP Server - Environment Configuration
# Please update these values with your actual credentials

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key_here
AWS_SECRET_ACCESS_KEY=your_aws_secret_key_here
AWS_DEFAULT_REGION=us-east-1

# AgentCore Gateway Configuration
DCISIONAI_ACCESS_TOKEN=your_access_token_here
DCISIONAI_GATEWAY_URL=https://dcisionai-gateway-0de1a655-ja1rhlcqjx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
DCISIONAI_GATEWAY_TARGET=DcisionAI-Optimization-Tools-Fixed

# Optional: Server Configuration
DCISIONAI_LOG_LEVEL=INFO
DCISIONAI_MAX_WORKERS=4
DCISIONAI_HOST=0.0.0.0
DCISIONAI_PORT=8000
EOF
    echo "✅ Created .env file at: $ENV_FILE"
    echo "⚠️  Please edit $ENV_FILE with your actual credentials"
else
    echo "✅ .env file already exists at: $ENV_FILE"
fi

# Test installation
echo "🧪 Testing installation..."
dcisionai-mcp-server --help > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ CLI test passed"
else
    echo "❌ CLI test failed"
    exit 1
fi

# Create Cursor MCP configuration
echo "🔧 Creating Cursor MCP configuration..."
CURSOR_CONFIG_DIR="$HOME/.cursor"
CURSOR_MCP_FILE="$CURSOR_CONFIG_DIR/mcp.json"

# Create .cursor directory if it doesn't exist
mkdir -p "$CURSOR_CONFIG_DIR"

# Check if mcp.json exists
if [ -f "$CURSOR_MCP_FILE" ]; then
    echo "✅ Cursor MCP configuration already exists at: $CURSOR_MCP_FILE"
    echo "⚠️  Please manually add the DcisionAI MCP server configuration"
else
    cat > "$CURSOR_MCP_FILE" << EOF
{
  "mcpServers": {
    "dcisionai-optimization": {
      "command": "python",
      "args": [
        "-m", "dcisionai_mcp_server.cli"
      ],
      "env": {
        "DCISIONAI_ACCESS_TOKEN": "your_access_token_here",
        "DCISIONAI_GATEWAY_URL": "https://dcisionai-gateway-0de1a655-ja1rhlcqjx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
        "DCISIONAI_GATEWAY_TARGET": "DcisionAI-Optimization-Tools-Fixed"
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
    echo "✅ Created Cursor MCP configuration at: $CURSOR_MCP_FILE"
    echo "⚠️  Please update the access token in the configuration"
fi

echo ""
echo "🎉 DcisionAI MCP Server installation completed successfully!"
echo ""
echo "📋 Next Steps:"
echo "1. Edit $ENV_FILE with your actual credentials"
echo "2. Update the access token in $CURSOR_MCP_FILE"
echo "3. Restart Cursor IDE to activate the MCP integration"
echo ""
echo "🧪 Test the installation:"
echo "   dcisionai-mcp-server --help"
echo "   dcisionai-mcp-server list-workflows"
echo "   dcisionai-mcp-server test-connection"
echo ""
echo "🚀 Start using optimization tools in Cursor!"
echo "   Ask: 'Help me optimize my supply chain costs'"
echo "   Ask: 'Show me available manufacturing workflows'"
echo "   Ask: 'Build a production planning model'"
