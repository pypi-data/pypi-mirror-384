#!/usr/bin/env python3
"""
DcisionAI MCP Server - Standard MCP Protocol Implementation
==========================================================

This module provides a standard MCP server implementation that communicates
via stdin/stdout, compatible with Cursor IDE and other MCP clients.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import mcp.types as types

from .tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization,
    select_solver,
    explain_optimization,
    get_workflow_templates,
    execute_workflow,
)
from .config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DcisionAIMCPServer:
    """
    DcisionAI MCP Server using standard MCP protocol.
    
    Provides 8 core tools for AI-powered business optimization:
    1. classify_intent - Intent classification for optimization requests
    2. analyze_data - Data analysis and preprocessing
    3. build_model - Mathematical model building with Qwen 30B
    4. solve_optimization - Optimization solving and results
    5. select_solver - Intelligent solver selection based on problem type
    6. explain_optimization - Business-facing explainability and insights
    7. get_workflow_templates - Industry workflow templates
    8. execute_workflow - End-to-end workflow execution
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the DcisionAI MCP Server."""
        self.config = config or Config()
        self.server = Server("dcisionai-optimization")
        self._register_handlers()
        logger.info("DcisionAI MCP Server initialized successfully")
    
    def _register_handlers(self):
        """Register MCP protocol handlers."""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List all available tools."""
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
                            },
                            "context": {
                                "type": "string",
                                "description": "Optional context about the business domain",
                                "default": None
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
                                "description": "Intent classification results from classify_intent",
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
                    name="select_solver",
                    description="Select the best available solver for optimization problems",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "optimization_type": {
                                "type": "string",
                                "description": "Type of optimization problem (linear_programming, quadratic_programming, mixed_integer_linear_programming, etc.)"
                            },
                            "problem_size": {
                                "type": "object",
                                "description": "Problem size information (num_variables, num_constraints, etc.)",
                                "default": {}
                            },
                            "performance_requirement": {
                                "type": "string",
                                "description": "Performance requirement: speed, accuracy, or balanced",
                                "default": "balanced"
                            }
                        },
                        "required": ["optimization_type"]
                    }
                ),
                Tool(
                    name="explain_optimization",
                    description="Provide business-facing explainability for optimization results",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "problem_description": {
                                "type": "string",
                                "description": "Original problem description"
                            },
                            "intent_data": {
                                "type": "object",
                                "description": "Results from intent classification",
                                "default": {}
                            },
                            "data_analysis": {
                                "type": "object",
                                "description": "Results from data analysis",
                                "default": {}
                            },
                            "model_building": {
                                "type": "object",
                                "description": "Results from model building",
                                "default": {}
                            },
                            "optimization_solution": {
                                "type": "object",
                                "description": "Results from optimization solving",
                                "default": {}
                            }
                        },
                        "required": ["problem_description"]
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
        
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls."""
            try:
                if name == "classify_intent":
                    result = await classify_intent(
                        arguments.get("problem_description", ""),
                        arguments.get("context")
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
                elif name == "select_solver":
                    result = await select_solver(
                        arguments.get("optimization_type", ""),
                        arguments.get("problem_size", {}),
                        arguments.get("performance_requirement", "balanced")
                    )
                elif name == "explain_optimization":
                    result = await explain_optimization(
                        arguments.get("problem_description", ""),
                        arguments.get("intent_data", {}),
                        arguments.get("data_analysis", {}),
                        arguments.get("model_building", {}),
                        arguments.get("optimization_solution", {})
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
                
                return [TextContent(type="text", text=result_text)]
                
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}")
                error_result = {
                    "error": f"Tool execution failed: {str(e)}",
                    "tool": name,
                    "arguments": arguments
                }
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]
    
    async def run(self):
        """Run the MCP server using stdio transport."""
        logger.info("Starting DcisionAI MCP Server with stdio transport")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(
                    read_stream,
                    write_stream,
                    InitializationOptions(
                        server_name="dcisionai-optimization",
                        server_version="1.0.0",
                        capabilities=self.server.get_capabilities(
                            notification_options=None,
                            experimental_capabilities={}
                        )
                    ),
                    raise_exceptions=True
                )
        except Exception as e:
            logger.error(f"Error in MCP server run: {e}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """Main entry point for the MCP server."""
    try:
        # Load configuration
        config = Config()
        
        # Create and run server
        server = DcisionAIMCPServer(config)
        asyncio.run(server.run())
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
