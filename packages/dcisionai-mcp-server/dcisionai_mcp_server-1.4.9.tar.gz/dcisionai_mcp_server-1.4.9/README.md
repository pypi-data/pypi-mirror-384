# DcisionAI MCP Server

[![PyPI version](https://badge.fury.io/py/dcisionai-mcp-server.svg)](https://badge.fury.io/py/dcisionai-mcp-server)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 AI-Powered Mathematical Optimization for Cursor IDE

The DcisionAI MCP Server brings advanced mathematical optimization capabilities directly to your Cursor IDE. Transform natural language problem descriptions into optimal solutions using state-of-the-art AI models and robust optimization solvers.

## ✨ Features

- **8 Powerful Tools**: Complete optimization workflow from problem understanding to business explanations
- **AI-Driven Problem Formulation**: Uses Claude 3 Haiku to translate business problems into mathematical models
- **Real Optimization Solvers**: OR-Tools integration with PDLP, GLOP, CBC, SCIP, and more
- **Business Explainability**: Generate executive summaries and implementation guidance
- **21 Industry Workflows**: Pre-built templates for manufacturing, healthcare, finance, and more
- **Cursor IDE Integration**: Seamless integration with Cursor's MCP protocol

## 🛠️ Available Tools

1. **`classify_intent`** - Understand and classify optimization problems
2. **`analyze_data`** - Assess data quality and identify variables/constraints
3. **`build_model`** - Generate mathematical optimization models using AI
4. **`select_solver`** - Choose the best solver for your problem type
5. **`solve_optimization`** - Execute optimization using real solvers
6. **`explain_optimization`** - Generate business-friendly explanations
7. **`get_workflow_templates`** - Access 21 industry-specific workflows
8. **`execute_workflow`** - Run complete optimization workflows

## 🚀 Quick Start

### Installation

```bash
# Install via pip
pip install dcisionai-mcp-server

# Or use uvx for direct execution
uvx dcisionai-mcp-server@latest
```

### Cursor IDE Setup

Add to your `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "dcisionai-mcp-server": {
      "command": "uvx",
      "args": ["dcisionai-mcp-server@latest"],
      "env": {
        "PYTHONUNBUFFERED": "1"
      },
      "disabled": false,
      "autoApprove": [
        "classify_intent",
        "analyze_data", 
        "build_model",
        "solve_optimization",
        "select_solver",
        "explain_optimization",
        "get_workflow_templates",
        "execute_workflow"
      ]
    }
  }
}
```

### Usage Example

```python
# In Cursor IDE, use the MCP tools:
@dcisionai-mcp-server classify_intent "Optimize my investment portfolio for maximum returns with moderate risk"

# Follow up with:
@dcisionai-mcp-server build_model "Portfolio optimization problem" --intent_data <previous_result>

# Continue the workflow:
@dcisionai-mcp-server solve_optimization "Portfolio problem" --model_building <model_result>
```

## 📊 Supported Optimization Types

- **Linear Programming (LP)** - Resource allocation, production planning
- **Mixed-Integer Linear Programming (MILP)** - Scheduling, routing
- **Quadratic Programming (QP)** - Portfolio optimization, risk management
- **Convex Optimization** - Machine learning, signal processing

## 🏭 Industry Workflows

- **Manufacturing**: Production planning, inventory optimization, quality control
- **Healthcare**: Staff scheduling, patient flow, resource allocation
- **Finance**: Portfolio optimization, risk assessment, fraud detection
- **Retail**: Demand forecasting, pricing optimization, supply chain
- **Logistics**: Route optimization, warehouse management, fleet operations
- **Energy**: Grid optimization, renewable integration, demand response
- **Marketing**: Campaign optimization, budget allocation, customer segmentation

## 🔧 Requirements

- Python 3.8+ (Python 3.13 has limited OR-Tools support)
- AWS credentials for Bedrock access (for AI model inference)
- Cursor IDE (for MCP integration)

## 📚 Documentation

- [Platform Overview](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/docs/PLATFORM_OVERVIEW.md)
- [API Reference](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/docs/API_REFERENCE.md)
- [Quick Start Guide](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/docs/QUICK_START.md)
- [Deployment Guide](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/docs/DEPLOYMENT_GUIDE.md)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](https://github.com/dcisionai/dcisionai-mcp-platform/blob/main/CONTRIBUTING.md).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/dcisionai/dcisionai-mcp-platform/issues)
- **Discussions**: [GitHub Discussions](https://github.com/dcisionai/dcisionai-mcp-platform/discussions)
- **Email**: contact@dcisionai.com

## 🙏 Acknowledgments

- [OR-Tools](https://developers.google.com/optimization) for optimization solvers
- [Claude 3 Haiku](https://www.anthropic.com/claude) for AI model inference
- [Cursor IDE](https://cursor.sh/) for MCP protocol support
- [AWS Bedrock](https://aws.amazon.com/bedrock/) for AI model hosting

---

**Made with ❤️ by the DcisionAI Team**