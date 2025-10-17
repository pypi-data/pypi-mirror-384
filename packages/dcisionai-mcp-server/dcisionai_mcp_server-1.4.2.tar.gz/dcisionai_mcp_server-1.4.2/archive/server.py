#!/usr/bin/env python3
"""
DcisionAI MCP Server
===================

Main MCP server implementation for AI-powered business optimization.
Provides industry-specific workflows with Qwen 30B integration.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from .tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization,
    get_workflow_templates,
    execute_workflow,
)
from .config import Config
from .workflows import WorkflowManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DcisionAIMCPServer:
    """
    DcisionAI MCP Server for AI-powered business optimization.
    
    Provides 6 core tools:
    1. classify_intent - Intent classification for optimization requests
    2. analyze_data - Data analysis and preprocessing
    3. build_model - Mathematical model building with Qwen 30B
    4. solve_optimization - Optimization solving and results
    5. get_workflow_templates - Industry workflow templates
    6. execute_workflow - End-to-end workflow execution
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the DcisionAI MCP Server."""
        self.config = config or Config()
        self.workflow_manager = WorkflowManager()
        self.mcp = FastMCP("DcisionAI Optimization Tools")
        
        # Register all tools
        self._register_tools()
        
        logger.info("DcisionAI MCP Server initialized successfully")
    
    def _register_tools(self):
        """Register all MCP tools with the server."""
        
        @self.mcp.tool()
        async def classify_intent_tool(
            user_input: str,
            context: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Classify user intent for optimization requests.
            
            Args:
                user_input: The user's optimization request
                context: Optional context about the business domain
                
            Returns:
                Classification result with intent type and confidence
            """
            return await classify_intent(user_input, context)
        
        @self.mcp.tool()
        async def analyze_data_tool(
            data_description: str,
            data_type: str = "tabular",
            constraints: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Analyze and preprocess data for optimization.
            
            Args:
                data_description: Description of the data to analyze
                data_type: Type of data (tabular, time_series, etc.)
                constraints: Optional constraints or requirements
                
            Returns:
                Data analysis results and recommendations
            """
            return await analyze_data(data_description, data_type, constraints)
        
        @self.mcp.tool()
        async def build_model_tool(
            problem_description: str,
            data_analysis: Optional[Dict[str, Any]] = None,
            model_type: Optional[str] = None
        ) -> Dict[str, Any]:
            """
            Build mathematical optimization model using Qwen 30B.
            
            Args:
                problem_description: Detailed problem description
                data_analysis: Results from data analysis step
                model_type: Preferred model type (optional)
                
            Returns:
                Model specification and mathematical formulation
            """
            return await build_model(problem_description, data_analysis, model_type)
        
        @self.mcp.tool()
        async def solve_optimization_tool(
            model_specification: Dict[str, Any],
            solver_config: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Solve the optimization problem and generate results.
            
            Args:
                model_specification: Model from build_model step
                solver_config: Optional solver configuration
                
            Returns:
                Optimization results and business insights
            """
            return await solve_optimization(model_specification, solver_config)
        
        @self.mcp.tool()
        async def get_workflow_templates_tool() -> Dict[str, Any]:
            """
            Get available industry workflow templates.
            
            Returns:
                List of available workflows organized by industry
            """
            return await get_workflow_templates()
        
        @self.mcp.tool()
        async def execute_workflow_tool(
            industry: str,
            workflow_id: str,
            parameters: Optional[Dict[str, Any]] = None
        ) -> Dict[str, Any]:
            """
            Execute a complete optimization workflow.
            
            Args:
                industry: Target industry (manufacturing, healthcare, etc.)
                workflow_id: Specific workflow to execute
                parameters: Optional workflow parameters
                
            Returns:
                Complete workflow execution results
            """
            return await execute_workflow(industry, workflow_id, parameters)
    
    async def run(self, host: str = "localhost", port: int = 8000):
        """Run the MCP server."""
        logger.info(f"Starting DcisionAI MCP Server on {host}:{port}")
        
        try:
            await self.mcp.run(host=host, port=port)
        except Exception as e:
            logger.error(f"Error running MCP server: {e}")
            raise
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities."""
        return {
            "name": "DcisionAI Optimization Tools",
            "version": "1.0.0",
            "description": "AI-powered business optimization with industry workflows",
            "capabilities": [
                "Intent Classification",
                "Data Analysis", 
                "Model Building (Qwen 30B)",
                "Optimization Solving",
                "Workflow Templates",
                "End-to-End Execution"
            ],
            "industries": [
                "Manufacturing",
                "Healthcare", 
                "Retail",
                "Marketing",
                "Financial",
                "Logistics",
                "Energy"
            ],
            "workflows": 21,
            "integrations": [
                "Qwen 30B",
                "AgentCore Gateway",
                "AWS Bedrock"
            ]
        }

# CLI entry point
async def main():
    """Main entry point for the MCP server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="DcisionAI MCP Server")
    parser.add_argument("--host", default="localhost", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Load configuration if provided
    config = None
    if args.config:
        config = Config.from_file(args.config)
    
    # Create and run server
    server = DcisionAIMCPServer(config)
    await server.run(host=args.host, port=args.port)

if __name__ == "__main__":
    asyncio.run(main())
