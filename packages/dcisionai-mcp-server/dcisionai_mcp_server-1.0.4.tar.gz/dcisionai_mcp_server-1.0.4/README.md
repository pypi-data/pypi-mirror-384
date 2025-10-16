# DcisionAI MCP Server

A Model Context Protocol (MCP) server that provides real mathematical optimization capabilities powered by OR-Tools and AI-driven problem formulation.

## Features

- **6 Core Optimization Tools**: Intent classification, data analysis, model building, optimization solving, workflow templates, and end-to-end execution
- **Real Mathematical Optimization**: Uses OR-Tools for genuine mathematical solving (not AI generation)
- **AI-Driven Formulation**: Leverages Qwen 30B for intelligent problem formulation
- **Industry Workflows**: Pre-built templates for manufacturing, healthcare, retail, marketing, financial, logistics, and energy sectors
- **MCP Protocol**: Seamless integration with AI development environments like Cursor

## Installation

```bash
pip install dcisionai-mcp-server
```

## Usage

The server can be run directly:

```bash
dcisionai-mcp-server
```

Or via uvx:

```bash
uvx dcisionai-mcp-server
```

## Configuration

Set the following environment variables:

- `AWS_ACCESS_KEY_ID`: Your AWS access key for Bedrock access
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key for Bedrock access  
- `AWS_REGION`: AWS region (default: us-east-1)

## Tools

1. **classify_intent**: Classify user intent for optimization requests
2. **analyze_data**: Analyze and preprocess data for optimization
3. **build_model**: Build mathematical optimization model using Qwen 30B
4. **solve_optimization**: Solve the optimization problem using OR-Tools
5. **get_workflow_templates**: Get available industry workflow templates
6. **execute_workflow**: Execute a complete optimization workflow

## License

MIT License