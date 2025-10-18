#!/bin/bash

# DcisionAI MCP Server - IDE Integration Setup
# One-click setup for various IDEs

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to setup Cursor IDE
setup_cursor() {
    print_status "Setting up Cursor IDE integration..."
    
    CURSOR_CONFIG_DIR="$HOME/.cursor"
    MCP_CONFIG_FILE="$CURSOR_CONFIG_DIR/mcp.json"
    
    # Create Cursor config directory if it doesn't exist
    mkdir -p "$CURSOR_CONFIG_DIR"
    
    # Backup existing config if it exists
    if [ -f "$MCP_CONFIG_FILE" ]; then
        cp "$MCP_CONFIG_FILE" "$MCP_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        print_warning "Backed up existing MCP configuration"
    fi
    
    # Create new MCP configuration
    cat > "$MCP_CONFIG_FILE" << 'EOF'
{
  "mcpServers": {
    "dcisionai-optimization": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server"],
      "autoApprove": [
        "classify_intent",
        "analyze_data", 
        "build_model",
        "solve_optimization",
        "get_workflow_templates",
        "execute_workflow"
      ],
      "env": {
        "DCISIONAI_ACCESS_TOKEN": "${DCISIONAI_ACCESS_TOKEN}",
        "DCISIONAI_GATEWAY_URL": "${DCISIONAI_GATEWAY_URL}",
        "DCISIONAI_GATEWAY_TARGET": "DcisionAI-Optimization-Tools-Fixed"
      }
    }
  }
}
EOF
    
    print_success "Cursor IDE integration configured"
    print_warning "Please restart Cursor IDE to activate the integration"
}

# Function to setup VS Code
setup_vscode() {
    print_status "Setting up VS Code integration..."
    
    VSCODE_CONFIG_DIR="$HOME/.vscode"
    MCP_CONFIG_FILE="$VSCODE_CONFIG_DIR/settings.json"
    
    # Create VS Code config directory if it doesn't exist
    mkdir -p "$VSCODE_CONFIG_DIR"
    
    # Backup existing config if it exists
    if [ -f "$MCP_CONFIG_FILE" ]; then
        cp "$MCP_CONFIG_FILE" "$MCP_CONFIG_FILE.backup.$(date +%Y%m%d_%H%M%S)"
        print_warning "Backed up existing VS Code settings"
    fi
    
    # Create or update settings.json
    if [ -f "$MCP_CONFIG_FILE" ]; then
        # Update existing settings.json
        python3 -c "
import json
import sys

try:
    with open('$MCP_CONFIG_FILE', 'r') as f:
        settings = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    settings = {}

# Add MCP server configuration
settings['mcp.servers'] = {
    'dcisionai-optimization': {
        'command': 'uvx',
        'args': ['dcisionai-mcp-server'],
        'autoApprove': [
            'classify_intent',
            'analyze_data',
            'build_model', 
            'solve_optimization',
            'get_workflow_templates',
            'execute_workflow'
        ],
        'env': {
            'DCISIONAI_ACCESS_TOKEN': '\${env:DCISIONAI_ACCESS_TOKEN}',
            'DCISIONAI_GATEWAY_URL': '\${env:DCISIONAI_GATEWAY_URL}',
            'DCISIONAI_GATEWAY_TARGET': 'DcisionAI-Optimization-Tools-Fixed'
        }
    }
}

with open('$MCP_CONFIG_FILE', 'w') as f:
    json.dump(settings, f, indent=2)
"
    else
        # Create new settings.json
        cat > "$MCP_CONFIG_FILE" << 'EOF'
{
  "mcp.servers": {
    "dcisionai-optimization": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server"],
      "autoApprove": [
        "classify_intent",
        "analyze_data",
        "build_model", 
        "solve_optimization",
        "get_workflow_templates",
        "execute_workflow"
      ],
      "env": {
        "DCISIONAI_ACCESS_TOKEN": "${env:DCISIONAI_ACCESS_TOKEN}",
        "DCISIONAI_GATEWAY_URL": "${env:DCISIONAI_GATEWAY_URL}",
        "DCISIONAI_GATEWAY_TARGET": "DcisionAI-Optimization-Tools-Fixed"
      }
    }
  }
}
EOF
    fi
    
    print_success "VS Code integration configured"
    print_warning "Please restart VS Code to activate the integration"
}

# Function to setup environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    ENV_FILE="$HOME/.dcisionai_env"
    
    # Create environment file
    cat > "$ENV_FILE" << 'EOF'
# DcisionAI MCP Server Environment Variables
# Add your credentials here

export DCISIONAI_ACCESS_TOKEN="your_jwt_access_token_here"
export DCISIONAI_GATEWAY_URL="https://your-gateway-url.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
export DCISIONAI_GATEWAY_TARGET="DcisionAI-Optimization-Tools-Fixed"

# Optional: AWS Configuration
export AWS_ACCESS_KEY_ID="your_aws_access_key_here"
export AWS_SECRET_ACCESS_KEY="your_aws_secret_key_here"
export AWS_DEFAULT_REGION="us-east-1"
EOF
    
    # Add to shell profile
    SHELL_PROFILE=""
    if [ -f "$HOME/.bashrc" ]; then
        SHELL_PROFILE="$HOME/.bashrc"
    elif [ -f "$HOME/.zshrc" ]; then
        SHELL_PROFILE="$HOME/.zshrc"
    elif [ -f "$HOME/.profile" ]; then
        SHELL_PROFILE="$HOME/.profile"
    fi
    
    if [ -n "$SHELL_PROFILE" ]; then
        if ! grep -q "dcisionai_env" "$SHELL_PROFILE"; then
            echo "" >> "$SHELL_PROFILE"
            echo "# DcisionAI MCP Server Environment" >> "$SHELL_PROFILE"
            echo "if [ -f ~/.dcisionai_env ]; then" >> "$SHELL_PROFILE"
            echo "    source ~/.dcisionai_env" >> "$SHELL_PROFILE"
            echo "fi" >> "$SHELL_PROFILE"
            print_success "Environment variables added to $SHELL_PROFILE"
        else
            print_warning "Environment variables already configured in $SHELL_PROFILE"
        fi
    fi
    
    print_success "Environment configuration created at $ENV_FILE"
    print_warning "Please edit $ENV_FILE with your actual credentials"
}

# Function to install uvx if not present
install_uvx() {
    print_status "Checking for uvx installation..."
    
    if command -v uvx &> /dev/null; then
        print_success "uvx is already installed"
        return 0
    fi
    
    print_warning "uvx not found. Installing..."
    
    # Install uvx
    if command -v pip &> /dev/null; then
        pip install uvx
    elif command -v pip3 &> /dev/null; then
        pip3 install uvx
    else
        print_error "pip not found. Please install Python and pip first."
        exit 1
    fi
    
    print_success "uvx installed successfully"
}

# Main setup function
main() {
    echo "🚀 DcisionAI MCP Server - IDE Integration Setup"
    echo "==============================================="
    echo
    
    # Install uvx
    install_uvx
    
    # Setup environment variables
    setup_environment
    
    # Ask user which IDE to setup
    echo "Which IDE would you like to configure?"
    echo "1) Cursor"
    echo "2) VS Code"
    echo "3) Both"
    echo "4) Skip IDE setup"
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            setup_cursor
            ;;
        2)
            setup_vscode
            ;;
        3)
            setup_cursor
            setup_vscode
            ;;
        4)
            print_warning "Skipping IDE setup"
            ;;
        *)
            print_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo
    print_success "🎉 IDE integration setup completed!"
    echo
    echo "Next steps:"
    echo "1. Edit ~/.dcisionai_env with your actual credentials"
    echo "2. Restart your IDE"
    echo "3. Test the integration by running: dcisionai-mcp-server health-check"
    echo
    echo "For more information, visit: https://github.com/DcisionAI/dcisionai-mcp-server"
}

# Run main function
main "$@"
