#!/usr/bin/env python3
"""
DcisionAI MCP Server - Robust Implementation
============================================

A robust MCP server implementation with better error handling and logging.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List
from mcp.server import Server
from mcp.server.models import InitializationOptions, ServerCapabilities
from mcp.types import ToolsCapability, Tool, TextContent
from mcp.server.stdio import stdio_server

from .tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization,
    get_workflow_templates,
    execute_workflow,
)

# Configure logging to stderr so it doesn't interfere with MCP protocol
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create server
server = Server("dcisionai-optimization")

@server.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List all available tools."""
    logger.info("Listing tools requested")
    return [
        Tool(
            name="classify_intent",
            description="Classify user intent for optimization requests",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "The user's optimization request or problem description"
                    }
                },
                "required": ["problem_description"]
            }
        ),
        Tool(
            name="analyze_data",
            description="Analyze and preprocess data for optimization",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "Description of the optimization problem"
                    },
                    "intent_data": {
                        "type": "object",
                        "description": "Intent classification results",
                        "default": {}
                    }
                },
                "required": ["problem_description"]
            }
        ),
        Tool(
            name="build_model",
            description="Build mathematical optimization model using Qwen 30B",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "Detailed problem description"
                    },
                    "intent_data": {
                        "type": "object",
                        "description": "Intent classification results",
                        "default": {}
                    },
                    "data_analysis": {
                        "type": "object",
                        "description": "Results from data analysis step",
                        "default": {}
                    }
                },
                "required": ["problem_description"]
            }
        ),
        Tool(
            name="solve_optimization",
            description="Solve the optimization problem and generate results",
            inputSchema={
                "type": "object",
                "properties": {
                    "problem_description": {
                        "type": "string",
                        "description": "Problem description"
                    },
                    "intent_data": {
                        "type": "object",
                        "description": "Intent classification results",
                        "default": {}
                    },
                    "data_analysis": {
                        "type": "object",
                        "description": "Data analysis results",
                        "default": {}
                    },
                    "model_building": {
                        "type": "object",
                        "description": "Model building results",
                        "default": {}
                    }
                },
                "required": ["problem_description"]
            }
        ),
        Tool(
            name="get_workflow_templates",
            description="Get available industry workflow templates",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="execute_workflow",
            description="Execute a complete optimization workflow",
            inputSchema={
                "type": "object",
                "properties": {
                    "industry": {
                        "type": "string",
                        "description": "Target industry (manufacturing, healthcare, retail, marketing, financial, logistics, energy)"
                    },
                    "workflow_id": {
                        "type": "string",
                        "description": "Specific workflow to execute"
                    },
                    "user_input": {
                        "type": "object",
                        "description": "User input parameters",
                        "default": {}
                    }
                },
                "required": ["industry", "workflow_id"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    logger.info(f"Tool call requested: {name}")
    try:
        if name == "classify_intent":
            result = await classify_intent(
                arguments.get("problem_description", ""),
                None
            )
        elif name == "analyze_data":
            result = await analyze_data(
                arguments.get("problem_description", ""),
                arguments.get("intent_data", {})
            )
        elif name == "build_model":
            result = await build_model(
                arguments.get("problem_description", ""),
                arguments.get("intent_data", {}),
                arguments.get("data_analysis", {})
            )
        elif name == "solve_optimization":
            result = await solve_optimization(
                arguments.get("problem_description", ""),
                arguments.get("intent_data", {}),
                arguments.get("data_analysis", {}),
                arguments.get("model_building", {})
            )
        elif name == "get_workflow_templates":
            result = await get_workflow_templates()
        elif name == "execute_workflow":
            result = await execute_workflow(
                arguments.get("industry", ""),
                arguments.get("workflow_id", ""),
                arguments.get("user_input", {})
            )
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Convert result to JSON string
        if isinstance(result, dict):
            result_text = json.dumps(result, indent=2)
        else:
            result_text = str(result)
        
        logger.info(f"Tool {name} executed successfully")
        return [TextContent(type="text", text=result_text)]
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        error_result = {
            "error": f"Tool execution failed: {str(e)}",
            "tool": name,
            "arguments": arguments
        }
        return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

async def main():
    """Main entry point for the MCP server."""
    logger.info("Starting DcisionAI MCP Server")
    
    try:
        async with stdio_server() as (read_stream, write_stream):
            logger.info("MCP Server stdio transport established")
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="dcisionai-optimization",
                    server_version="1.0.0",
                    capabilities=ServerCapabilities(
                        tools=ToolsCapability()
                    )
                )
            )
    except Exception as e:
        logger.error(f"Error running MCP server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
