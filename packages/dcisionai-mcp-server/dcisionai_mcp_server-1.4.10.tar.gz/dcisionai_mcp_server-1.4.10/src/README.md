# DcisionAI MCP Server

[![PyPI version](https://badge.fury.io/py/dcisionai-mcp-server.svg)](https://badge.fury.io/py/dcisionai-mcp-server)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for AI-powered business optimization with industry-specific workflows and Qwen 30B integration.

## 🚀 Features

- **21 Pre-built Workflows** across 7 industries (Manufacturing, Healthcare, Retail, Marketing, Financial, Logistics, Energy)
- **Qwen 30B Integration** for superior mathematical reasoning and optimization
- **AgentCore Gateway** integration for cloud-native deployment
- **6 Core Tools** for complete optimization pipeline
- **Production Ready** with comprehensive error handling and logging
- **Multi-IDE Support** (Cursor, Kiro, Claude Code, VS Code)

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Available Tools](#available-tools)
- [Workflow Examples](#workflow-examples)
- [IDE Integration](#ide-integration)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## 🛠 Installation

### 🚀 Option 1: One-Click Auto-Installer (Recommended)

The auto-installer handles all dependencies automatically:

```bash
# Download and run the auto-installer
curl -fsSL https://raw.githubusercontent.com/DcisionAI/dcisionai-mcp-server/main/install.sh | bash
```

This script will:
- ✅ Install Python 3.8+ if needed
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up configuration
- ✅ Run health checks
- ✅ Configure IDE integration

### 🐳 Option 2: Docker (Zero Dependencies)

Perfect for production deployment:

```bash
# Clone the repository
git clone https://github.com/DcisionAI/dcisionai-mcp-server.git
cd dcisionai-mcp-server

# Run with Docker Compose (handles all dependencies automatically)
docker-compose up -d
```

### 📦 Option 3: Traditional pip Installation

```bash
pip install dcisionai-mcp-server
```

### 🔧 Option 4: Development Installation

```bash
git clone https://github.com/DcisionAI/dcisionai-mcp-server.git
cd dcisionai-mcp-server
pip install -e .
```

## 🔍 Setup Validation

After installation, validate your setup with our comprehensive validation script:

```bash
# Run the validation script
python validate-setup.py
```

This will check:
- ✅ System requirements
- ✅ Python environment
- ✅ Dependencies
- ✅ Configuration
- ✅ AWS credentials
- ✅ AgentCore Gateway connection
- ✅ MCP server functionality
- ✅ IDE integration
- ✅ Docker setup
- ✅ Cloud deployment readiness

## 🚀 Quick Start

### 1. Start the Server

```bash
# Using CLI
dcisionai-mcp-server start --host 0.0.0.0 --port 8000

# Using Python
from dcisionai_mcp_server import DcisionAIMCPServer
import asyncio

async def main():
    server = DcisionAIMCPServer()
    await server.run(host="localhost", port=8000)

asyncio.run(main())
```

### 2. List Available Workflows

```bash
dcisionai-mcp-server list-workflows
```

### 3. Test Connection

```bash
dcisionai-mcp-server test-connection
```

## ⚙️ Configuration

### Environment Variables

```bash
# Required
export DCISIONAI_ACCESS_TOKEN="your-access-token"
export DCISIONAI_GATEWAY_URL="https://your-gateway-url/mcp"
export DCISIONAI_GATEWAY_TARGET="your-gateway-target"

# Optional
export DCISIONAI_HOST="localhost"
export DCISIONAI_PORT="8000"
export DCISIONAI_LOG_LEVEL="INFO"
export DCISIONAI_DEBUG="false"
```

### Configuration File

Create `config.yaml`:

```yaml
gateway_url: "https://dcisionai-gateway-0de1a655-ja1rhlcqjx.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp"
gateway_target: "DcisionAI-Optimization-Tools-Fixed"
access_token: "your-access-token"
host: "localhost"
port: 8000
debug: false
log_level: "INFO"
aws_region: "us-east-1"
request_timeout: 30
```

## 🛠 Available Tools

### 1. `classify_intent`
Classify user intent for optimization requests.

```python
result = await classify_intent(
    user_input="Optimize our production schedule",
    context="manufacturing"
)
```

### 2. `analyze_data`
Analyze and preprocess data for optimization.

```python
result = await analyze_data(
    data_description="Production data with 1000 records",
    data_type="tabular",
    constraints="Must maintain quality standards"
)
```

### 3. `build_model`
Build mathematical optimization model using Qwen 30B.

```python
result = await build_model(
    problem_description="Minimize production costs while meeting demand",
    data_analysis=analysis_result,
    model_type="mixed_integer_programming"
)
```

### 4. `solve_optimization`
Solve the optimization problem and generate results.

```python
result = await solve_optimization(
    model_specification=model_result,
    solver_config={"time_limit": 300}
)
```

### 5. `get_workflow_templates`
Get available industry workflow templates.

```python
result = await get_workflow_templates()
```

### 6. `execute_workflow`
Execute a complete optimization workflow.

```python
result = await execute_workflow(
    industry="manufacturing",
    workflow_id="production_planning",
    parameters={"time_horizon": 30}
)
```

## 📊 Workflow Examples

### Manufacturing - Production Planning

```python
# Execute production planning optimization
result = await execute_workflow(
    industry="manufacturing",
    workflow_id="production_planning",
    parameters={
        "time_horizon": 30,
        "demand_forecast": "high_accuracy",
        "resource_constraints": "strict"
    }
)
```

### Healthcare - Staff Scheduling

```python
# Optimize healthcare staff schedules
result = await execute_workflow(
    industry="healthcare",
    workflow_id="staff_scheduling",
    parameters={
        "shift_length": 8,
        "minimum_staff": 5,
        "skill_requirements": "certified"
    }
)
```

### Retail - Pricing Optimization

```python
# Optimize retail pricing strategies
result = await execute_workflow(
    industry="retail",
    workflow_id="pricing_optimization",
    parameters={
        "price_elasticity": "high",
        "competitor_analysis": "enabled",
        "margin_target": 0.25
    }
)
```

## 🔌 IDE Integration

### Cursor Integration

Add to `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dcisionai-optimization": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server@latest"],
      "env": {
        "DCISIONAI_ACCESS_TOKEN": "your-access-token"
      },
      "autoApprove": [
        "execute_workflow",
        "get_workflow_templates"
      ]
    }
  }
}
```

### Kiro Integration

Add to `.kiro/settings/mcp.json`:

```json
{
  "mcpServers": {
    "dcisionai-optimization": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server@latest"],
      "env": {
        "DCISIONAI_ACCESS_TOKEN": "your-access-token"
      }
    }
  }
}
```

### VS Code Extension

Install the DcisionAI MCP extension from the VS Code marketplace.

## 📚 API Reference

### Server Class

```python
class DcisionAIMCPServer:
    def __init__(self, config: Optional[Config] = None)
    async def run(self, host: str = "localhost", port: int = 8000)
    def get_server_info(self) -> Dict[str, Any]
```

### Configuration Class

```python
class Config:
    gateway_url: str
    gateway_target: str
    access_token: str
    host: str = "localhost"
    port: int = 8000
    debug: bool = False
```

### Workflow Manager

```python
class WorkflowManager:
    def get_all_workflows(self) -> Dict[str, Any]
    def get_industry_workflows(self, industry: str) -> Dict[str, Any]
    def get_workflow_details(self, industry: str, workflow_id: str) -> Dict[str, Any]
    def search_workflows(self, query: str) -> List[Dict[str, Any]]
```

## 🏭 Supported Industries

| Industry | Workflows | Complexity | Use Cases |
|----------|-----------|------------|-----------|
| **Manufacturing** | 3 | High | Production planning, inventory optimization, quality control |
| **Healthcare** | 3 | High | Staff scheduling, patient flow, resource allocation |
| **Retail** | 3 | Medium | Demand forecasting, pricing optimization, supply chain |
| **Marketing** | 3 | Medium | Campaign optimization, budget allocation, customer segmentation |
| **Financial** | 3 | High | Portfolio optimization, risk assessment, fraud detection |
| **Logistics** | 3 | High | Route optimization, warehouse optimization, fleet management |
| **Energy** | 3 | High | Grid optimization, renewable integration, demand response |

## 🔧 CLI Commands

```bash
# Start server
dcisionai-mcp-server start [--host HOST] [--port PORT] [--config CONFIG]

# List workflows
dcisionai-mcp-server list-workflows

# Show workflow details
dcisionai-mcp-server show-workflow INDUSTRY WORKFLOW_ID

# Search workflows
dcisionai-mcp-server search QUERY

# Show statistics
dcisionai-mcp-server stats

# Test connection
dcisionai-mcp-server test-connection
```

## 🧪 Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=dcisionai_mcp_server tests/

# Run specific test
pytest tests/test_tools.py::test_classify_intent
```

## 📈 Performance

- **Response Time**: 0.5-3.8 seconds per tool call
- **Throughput**: 100+ requests per minute
- **Availability**: 99.9% uptime
- **Scalability**: Auto-scaling with AgentCore Gateway

## 🔒 Security

- **Authentication**: JWT token-based authentication
- **Authorization**: Role-based access control
- **Encryption**: TLS 1.3 for all communications
- **Rate Limiting**: Configurable rate limits
- **Audit Logging**: Comprehensive audit trails

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/dcisionai/dcisionai-mcp-server.git
cd dcisionai-mcp-server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
pre-commit install
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://docs.dcisionai.com](https://docs.dcisionai.com)
- **Issues**: [GitHub Issues](https://github.com/dcisionai/dcisionai-mcp-server/issues)
- **Discord**: [DcisionAI Community](https://discord.gg/dcisionai)
- **Email**: support@dcisionai.com

## 🙏 Acknowledgments

- **AWS Bedrock** for AI model infrastructure
- **Qwen 30B** for mathematical optimization capabilities
- **AgentCore Gateway** for cloud-native deployment
- **MCP Protocol** for seamless IDE integration

---

**Made with ❤️ by the DcisionAI Team**

[Website](https://platform.dcisionai.com) • [Documentation](https://docs.dcisionai.com) • [GitHub](https://github.com/dcisionai/dcisionai-mcp-server)
