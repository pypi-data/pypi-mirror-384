#!/usr/bin/env python3
"""
Working DcisionAI MCP Server - Direct stdio implementation
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DcisionAIMCPServer:
    """Working DcisionAI MCP Server with direct stdio implementation."""
    
    def __init__(self):
        self.tools = [
            {
                "name": "classify_intent",
                "description": "Classify user intent for optimization requests",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {
                            "type": "string",
                            "description": "The user's optimization request or problem description"
                        },
                        "context": {
                            "type": "string",
                            "description": "Optional context about the business domain"
                        }
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "analyze_data",
                "description": "Analyze and preprocess data for optimization",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {
                            "type": "string",
                            "description": "Description of the optimization problem"
                        },
                        "intent_data": {
                            "type": "object",
                            "description": "Intent classification results from classify_intent"
                        }
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "build_model",
                "description": "Build mathematical optimization model using Qwen 30B",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {
                            "type": "string",
                            "description": "Detailed problem description"
                        },
                        "intent_data": {
                            "type": "object",
                            "description": "Intent classification results"
                        },
                        "data_analysis": {
                            "type": "object",
                            "description": "Results from data analysis step"
                        }
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "solve_optimization",
                "description": "Solve the optimization problem and generate results",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {
                            "type": "string",
                            "description": "Problem description"
                        },
                        "intent_data": {
                            "type": "object",
                            "description": "Intent classification results"
                        },
                        "data_analysis": {
                            "type": "object",
                            "description": "Data analysis results"
                        },
                        "model_building": {
                            "type": "object",
                            "description": "Model building results"
                        }
                    },
                    "required": ["problem_description"]
                }
            },
            {
                "name": "get_workflow_templates",
                "description": "Get available industry workflow templates",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "select_solver",
                "description": "Select the best available solver for optimization problems",
                "inputSchema": {
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
            },
            {
                "name": "explain_optimization",
                "description": "Provide business-facing explainability for optimization results",
                "inputSchema": {
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
            },
            {
                "name": "execute_workflow",
                "description": "Execute a complete optimization workflow",
                "inputSchema": {
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
                            "description": "User input parameters"
                        }
                    },
                    "required": ["industry", "workflow_id"]
                }
            }
        ]
    
    async def handle_initialize(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    }
                },
                "serverInfo": {
                    "name": "dcisionai-optimization",
                    "version": "1.3.4"
                }
            }
        }
    
    async def handle_tools_list(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        return {
            "jsonrpc": "2.0",
            "id": message.get("id"),
            "result": {
                "tools": self.tools
            }
        }
    
    async def handle_tools_call(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        params = message.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        try:
            logger.info(f"Calling tool: {tool_name} with arguments: {arguments}")
            
            # Import the actual tools only when needed
            try:
                import sys
                import os
                # Add the current directory to the path
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                
                from dcisionai_mcp_server.tools import (
                    classify_intent,
                    analyze_data,
                    build_model,
                    solve_optimization,
                    select_solver,
                    explain_optimization,
                    get_workflow_templates,
                    execute_workflow
                )
                logger.info("Tools imported successfully")
            except Exception as import_error:
                logger.error(f"Failed to import tools: {import_error}")
                return {
                    "jsonrpc": "2.0",
                    "id": message.get("id"),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({
                                    "error": f"Failed to import tools: {str(import_error)}",
                                    "tool": tool_name
                                }, indent=2)
                            }
                        ]
                    }
                }
            
            # Call the appropriate tool
            if tool_name == "classify_intent":
                result = await classify_intent(
                    arguments.get("problem_description", ""),
                    arguments.get("context")
                )
            elif tool_name == "analyze_data":
                result = await analyze_data(
                    arguments.get("problem_description", ""),
                    arguments.get("intent_data", {})
                )
            elif tool_name == "build_model":
                result = await build_model(
                    arguments.get("problem_description", ""),
                    arguments.get("intent_data", {}),
                    arguments.get("data_analysis", {})
                )
            elif tool_name == "solve_optimization":
                result = await solve_optimization(
                    arguments.get("problem_description", ""),
                    arguments.get("intent_data", {}),
                    arguments.get("data_analysis", {}),
                    arguments.get("model_building", {})
                )
            elif tool_name == "select_solver":
                result = await select_solver(
                    arguments.get("optimization_type", ""),
                    arguments.get("problem_size", {}),
                    arguments.get("performance_requirement", "balanced")
                )
            elif tool_name == "explain_optimization":
                result = await explain_optimization(
                    arguments.get("problem_description", ""),
                    arguments.get("intent_data", {}),
                    arguments.get("data_analysis", {}),
                    arguments.get("model_building", {}),
                    arguments.get("optimization_solution", {})
                )
            elif tool_name == "get_workflow_templates":
                result = await get_workflow_templates()
            elif tool_name == "execute_workflow":
                result = await execute_workflow(
                    arguments.get("industry", ""),
                    arguments.get("workflow_id", ""),
                    arguments.get("user_input", {})
                )
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
            
            logger.info(f"Tool {tool_name} executed successfully")
            
            # Convert result to JSON string
            if isinstance(result, dict):
                result_text = json.dumps(result, indent=2)
            else:
                result_text = str(result)
            
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            import traceback
            traceback.print_exc()
            error_result = {
                "error": f"Tool execution failed: {str(e)}",
                "tool": tool_name,
                "arguments": arguments
            }
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(error_result, indent=2)
                        }
                    ]
                }
            }
    
    async def run(self):
        """Run the MCP server with direct stdio."""
        logger.info("Starting DcisionAI MCP Server")
        
        # Read from stdin and write to stdout directly
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    logger.info("No more input, exiting")
                    break
                
                logger.info(f"Received raw line: {repr(line)}")
                
                # Parse JSON-RPC message
                try:
                    message = json.loads(line.strip())
                    logger.info(f"Received message: {message.get('method', 'unknown')}")
                    
                    method = message.get("method")
                    
                    if method == "initialize":
                        logger.info("Handling initialize request")
                        response = await self.handle_initialize(message)
                    elif method == "tools/list":
                        logger.info("Handling tools/list request")
                        response = await self.handle_tools_list(message)
                    elif method == "tools/call":
                        logger.info("Handling tools/call request")
                        response = await self.handle_tools_call(message)
                    else:
                        logger.warning(f"Unknown method: {method}")
                        response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "error": {
                                "code": -32601,
                                "message": f"Method not found: {method}"
                            }
                        }
                    
                    logger.info(f"Sending response: {json.dumps(response, indent=2)}")
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    continue
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                import traceback
                traceback.print_exc()
                break

def main():
    """Main entry point."""
    server = DcisionAIMCPServer()
    
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
