#!/bin/bash

# DcisionAI MCP Server - Seamless Auto-Installer
# This script handles all dependencies and setup automatically

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
    echo $OS
}

# Function to install Python if not present
install_python() {
    local os=$1
    print_status "Checking Python installation..."
    
    if command_exists python3 && python3 --version | grep -q "3.8\|3.9\|3.10\|3.11\|3.12"; then
        print_success "Python 3.8+ is already installed: $(python3 --version)"
        return 0
    fi
    
    print_warning "Python 3.8+ not found. Installing..."
    
    case $os in
        "linux")
            if command_exists apt-get; then
                sudo apt-get update
                sudo apt-get install -y python3 python3-pip python3-venv
            elif command_exists yum; then
                sudo yum install -y python3 python3-pip
            elif command_exists dnf; then
                sudo dnf install -y python3 python3-pip
            else
                print_error "Package manager not found. Please install Python 3.8+ manually."
                exit 1
            fi
            ;;
        "macos")
            if command_exists brew; then
                brew install python3
            else
                print_error "Homebrew not found. Please install Python 3.8+ manually or install Homebrew first."
                exit 1
            fi
            ;;
        "windows")
            print_error "Windows detected. Please install Python 3.8+ from https://python.org"
            exit 1
            ;;
        *)
            print_error "Unsupported OS. Please install Python 3.8+ manually."
            exit 1
            ;;
    esac
    
    print_success "Python installation completed"
}

# Function to install Docker if not present
install_docker() {
    local os=$1
    print_status "Checking Docker installation..."
    
    if command_exists docker && docker --version >/dev/null 2>&1; then
        print_success "Docker is already installed: $(docker --version)"
        return 0
    fi
    
    print_warning "Docker not found. Installing..."
    
    case $os in
        "linux")
            # Install Docker using official script
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            ;;
        "macos")
            if command_exists brew; then
                brew install --cask docker
            else
                print_error "Homebrew not found. Please install Docker Desktop manually from https://docker.com"
                exit 1
            fi
            ;;
        "windows")
            print_error "Windows detected. Please install Docker Desktop from https://docker.com"
            exit 1
            ;;
    esac
    
    print_success "Docker installation completed"
}

# Function to create virtual environment
setup_venv() {
    print_status "Setting up Python virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf venv
    fi
    
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    print_success "Virtual environment created and activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing DcisionAI MCP Server dependencies..."
    
    # Install the package in development mode
    pip install -e .
    
    print_success "Dependencies installed successfully"
}

# Function to setup configuration
setup_config() {
    print_status "Setting up configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f "env.example" ]; then
            cp env.example .env
            print_success "Configuration file created from template"
            
            # Set up environment variables for current session
            export DCISIONAI_ACCESS_TOKEN="eyJraWQiOiJLMWZEMFwvXC9qaGtJSHlZd2IyM2NsMkRSK0dEQ2tFaHVWZVd0djdFMERkOUk9IiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiI1cjdyaXJqdmI0OTZpam1rMDNtanNrNTNtOCIsInRva2VuX3VzZSI6ImFjY2VzcyIsInNjb3BlIjoiRGNpc2lvbkFJLUdhdGV3YXktMGRlMWE2NTVcL2ludm9rZSIsImF1dGhfdGltZSI6MTc2MDU0NzgwOCwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfdjlDSmJRMWVKIiwiZXhwIjoxNzYwNTUxNDA4LCJpYXQiOjE3NjA1NDc4MDgsInZlcnNpb24iOjIsImp0aSI6IjIzMDAwOTBmLWZjNzYtNDI1NC1hZjQ3LTY2ZDA5MGVkNzRiMiIsImNsaWVudF9pZCI6IjVyN3Jpcmp2YjQ5NmlqbWswM21qc2s1M204In0.nOgW15NAgzd-fB3Vn8fx0030rmX3_h9nKRkIM_JK3mXdATw-K0rCrinzll9XrN1m4pAOmVJFdoq0YbH7SOI6bMIl840TnN9hSxnKVy1zx5nOPn98btAKzP41UbLVJ8PGE3zAfrkOPtMaqvoMDzgCZP0fFF_FiCPFUWUvSs-OmbR2TnuVmdnuFCXLAQ_CMTJVpwVMk13P3mfJgkSPY33ly3GbtaVN9LDq11ZzVCAvsRbA7DvEWdSc9GVpHYmRwfEJYZZW4KNeOFZZRqZuryY57mBgcUaZ06deesl_ySN72a2CgJ1xnVCeK5VYcwdlUmQrSvEYxAJJGvF-ZacgQC6qUA"
            export DCISIONAI_GATEWAY_URL="https://dcisionai-gateway-0de1a655-ja1rhlcqjx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
            export DCISIONAI_GATEWAY_TARGET="DcisionAI-Optimization-Tools-Fixed"
            print_success "Environment variables set for current session"
            print_warning "Please edit .env file with your actual AWS credentials"
        else
            print_warning "No configuration template found. You'll need to create .env manually."
        fi
    else
        print_success "Configuration file already exists"
    fi
}

# Function to run health check
run_health_check() {
    print_status "Running health check..."
    
    if [ -f ".env" ]; then
        source .env
        source venv/bin/activate
        
        # Test connection
        if dcisionai-mcp-server test-connection >/dev/null 2>&1; then
            print_success "Health check passed - MCP Server is ready!"
        else
            print_warning "Health check failed - please check your configuration in .env"
        fi
    else
        print_warning "No .env file found - skipping health check"
    fi
}

# Function to show usage instructions
show_usage() {
    echo
    print_success "🎉 DcisionAI MCP Server installation completed!"
    echo
    echo "Next steps:"
    echo "1. Edit .env file with your credentials:"
    echo "   - AWS_ACCESS_KEY_ID"
    echo "   - AWS_SECRET_ACCESS_KEY"
    echo "   - DCISIONAI_ACCESS_TOKEN"
    echo "   - DCISIONAI_GATEWAY_URL"
    echo
    echo "2. Start the server:"
    echo "   source venv/bin/activate"
    echo "   dcisionai-mcp-server start"
    echo
    echo "3. Or use Docker:"
    echo "   docker-compose up -d"
    echo
    echo "4. Test the installation:"
    echo "   dcisionai-mcp-server test-connection"
    echo "   dcisionai-mcp-server list-workflows"
    echo
    echo "For more information, visit: https://github.com/DcisionAI/dcisionai-mcp-server"
}

# Main installation function
main() {
    echo "🚀 DcisionAI MCP Server - Seamless Auto-Installer"
    echo "=================================================="
    echo
    
    # Detect OS
    OS=$(detect_os)
    print_status "Detected OS: $OS"
    
    # Install Python
    install_python $OS
    
    # Install Docker (optional)
    read -p "Do you want to install Docker for containerized deployment? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        install_docker $OS
    fi
    
    # Setup virtual environment
    setup_venv
    
    # Install dependencies
    install_dependencies
    
    # Setup configuration
    setup_config
    
    # Run health check
    run_health_check
    
    # Show usage instructions
    show_usage
}

# Run main function
main "$@"
