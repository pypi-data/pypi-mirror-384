#!/usr/bin/env python3
"""
AgentCore Backend Proxy
=======================

This proxy service connects the frontend to the AgentCore runtime,
providing a bridge between the MCP protocol and the AgentCore API.

Author: DcisionAI Team
Copyright (c) 2025 DcisionAI. All rights reserved.
"""

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | AgentCore Proxy | %(message)s"
)
logger = logging.getLogger(__name__)

class AgentCoreBackendProxy:
    """
    Backend proxy that connects frontend to AgentCore runtime.
    
    This service provides a bridge between the MCP protocol used by the frontend
    and the AgentCore API, enabling seamless integration.
    """
    
    def __init__(self, agentcore_url: str = "http://localhost:8080"):
        self.app = FastAPI(
            title="AgentCore Backend Proxy",
            description="Proxy service connecting frontend to AgentCore runtime",
            version="1.0.0"
        )
        
        self.agentcore_url = agentcore_url
        self.client = httpx.AsyncClient(timeout=60.0)
        
        # Setup FastAPI
        self._setup_fastapi()
        
        logger.info(f"🚀 AgentCore Backend Proxy initialized")
        logger.info(f"🎯 AgentCore URL: {agentcore_url}")
    
    def _setup_fastapi(self):
        """Setup FastAPI application with middleware and routes."""
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Routes
        self.app.get("/health")(self.health_check)
        self.app.post("/mcp")(self.mcp_proxy)
        self.app.get("/status")(self.get_status)
        
        # Startup event
        self.app.add_event_handler("startup", self.startup)
        self.app.add_event_handler("shutdown", self.shutdown)
    
    async def startup(self):
        """Startup event handler."""
        logger.info("🚀 AgentCore Backend Proxy starting up...")
        
        # Test connection to AgentCore
        try:
            response = await self.client.get(f"{self.agentcore_url}/health")
            if response.status_code == 200:
                logger.info("✅ Connected to AgentCore runtime")
            else:
                logger.warning(f"⚠️ AgentCore health check returned status {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to AgentCore: {e}")
            logger.error("⚠️ AgentCore runtime may not be running on port 8080")
    
    async def shutdown(self):
        """Shutdown event handler."""
        logger.info("🛑 AgentCore Backend Proxy shutting down...")
        await self.client.aclose()
    
    async def health_check(self):
        """Health check endpoint."""
        try:
            # Check AgentCore health
            response = await self.client.get(f"{self.agentcore_url}/health")
            if response.status_code == 200:
                agentcore_health = response.json()
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "AgentCore Backend Proxy",
                    "agentcore_status": agentcore_health.get("status", "unknown"),
                    "agentcore_uptime": agentcore_health.get("uptime_seconds", 0)
                }
            else:
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "AgentCore Backend Proxy",
                    "error": f"AgentCore returned status {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "service": "AgentCore Backend Proxy",
                "error": str(e)
            }
    
    async def mcp_proxy(self, request: Request):
        """Proxy MCP requests to AgentCore runtime."""
        try:
            # Parse the MCP request
            mcp_request = await request.json()
            logger.info(f"🔄 MCP request: {mcp_request.get('method', 'unknown')}")
            
            # Handle different MCP methods
            method = mcp_request.get("method", "")
            
            if method == "tools/call":
                return await self._handle_tool_call(mcp_request)
            elif method == "tools/list":
                return await self._handle_tools_list(mcp_request)
            else:
                return JSONResponse(
                    status_code=400,
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ MCP proxy error: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }
            )
    
    async def _handle_tool_call(self, mcp_request: Dict[str, Any]):
        """Handle MCP tool call requests."""
        try:
            params = mcp_request.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            
            logger.info(f"🔧 Tool call: {tool_name}")
            
            # Map MCP tool names to AgentCore endpoints
            if tool_name == "manufacturing_optimize":
                return await self._call_agentcore_optimize(mcp_request, arguments)
            elif tool_name == "manufacturing_health_check":
                return await self._call_agentcore_health(mcp_request)
            elif tool_name == "get_optimization_insights":
                return await self._call_agentcore_insights(mcp_request, arguments)
            elif tool_name == "get_cache_insights":
                return await self._call_agentcore_cache_insights(mcp_request)
            elif tool_name == "get_coordination_insights":
                return await self._call_agentcore_coordination_insights(mcp_request)
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32601,
                            "message": f"Tool not found: {tool_name}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ Tool call error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Tool call failed: {str(e)}"
                    }
                }
            )
    
    async def _call_agentcore_optimize(self, mcp_request: Dict[str, Any], arguments: Dict[str, Any]):
        """Call AgentCore optimization endpoint."""
        try:
            # Convert MCP arguments to AgentCore format
            agentcore_request = {
                "problem_description": arguments.get("problem_description", ""),
                "constraints": arguments.get("constraints", {}),
                "optimization_goals": arguments.get("optimization_goals", []),
                "session_id": arguments.get("session_id"),
                "priority": 5
            }
            
            # Call AgentCore
            response = await self.client.post(
                f"{self.agentcore_url}/optimize",
                json=agentcore_request
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Convert AgentCore response to MCP format
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result)
                                }
                            ]
                        }
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"AgentCore optimization failed: {response.status_code}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ AgentCore optimization error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Optimization failed: {str(e)}"
                    }
                }
            )
    
    async def _call_agentcore_health(self, mcp_request: Dict[str, Any]):
        """Call AgentCore health check."""
        try:
            response = await self.client.get(f"{self.agentcore_url}/health")
            
            if response.status_code == 200:
                result = response.json()
                
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result)
                                }
                            ]
                        }
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"AgentCore health check failed: {response.status_code}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ AgentCore health check error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Health check failed: {str(e)}"
                    }
                }
            )
    
    async def _call_agentcore_insights(self, mcp_request: Dict[str, Any], arguments: Dict[str, Any]):
        """Call AgentCore insights endpoint."""
        try:
            # For now, just call the general insights endpoint
            response = await self.client.get(f"{self.agentcore_url}/insights")
            
            if response.status_code == 200:
                result = response.json()
                
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result)
                                }
                            ]
                        }
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"AgentCore insights failed: {response.status_code}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ AgentCore insights error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Insights failed: {str(e)}"
                    }
                }
            )
    
    async def _call_agentcore_cache_insights(self, mcp_request: Dict[str, Any]):
        """Call AgentCore cache insights."""
        try:
            response = await self.client.get(f"{self.agentcore_url}/metrics")
            
            if response.status_code == 200:
                result = response.json()
                cache_insights = result.get("cache_insights", {})
                
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(cache_insights)
                                }
                            ]
                        }
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"AgentCore cache insights failed: {response.status_code}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ AgentCore cache insights error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Cache insights failed: {str(e)}"
                    }
                }
            )
    
    async def _call_agentcore_coordination_insights(self, mcp_request: Dict[str, Any]):
        """Call AgentCore coordination insights."""
        try:
            response = await self.client.get(f"{self.agentcore_url}/metrics")
            
            if response.status_code == 200:
                result = response.json()
                coordination_insights = result.get("coordination_insights", {})
                
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(coordination_insights)
                                }
                            ]
                        }
                    }
                )
            else:
                return JSONResponse(
                    content={
                        "jsonrpc": "2.0",
                        "id": mcp_request.get("id"),
                        "error": {
                            "code": -32603,
                            "message": f"AgentCore coordination insights failed: {response.status_code}"
                        }
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ AgentCore coordination insights error: {e}")
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "id": mcp_request.get("id", 1),
                    "error": {
                        "code": -32603,
                        "message": f"Coordination insights failed: {str(e)}"
                    }
                }
            )
    
    async def _handle_tools_list(self, mcp_request: Dict[str, Any]):
        """Handle MCP tools list request."""
        tools = [
            {
                "name": "manufacturing_optimize",
                "description": "Optimize manufacturing processes using AgentCore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "problem_description": {"type": "string"},
                        "constraints": {"type": "object"},
                        "optimization_goals": {"type": "array"},
                        "session_id": {"type": "string"}
                    }
                }
            },
            {
                "name": "manufacturing_health_check",
                "description": "Check AgentCore health status",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_optimization_insights",
                "description": "Get optimization insights from AgentCore",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "intent": {"type": "string"}
                    }
                }
            },
            {
                "name": "get_cache_insights",
                "description": "Get cache performance insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_coordination_insights",
                "description": "Get agent coordination insights",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]
        
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": mcp_request.get("id"),
                "result": {
                    "tools": tools
                }
            }
        )
    
    async def get_status(self):
        """Get proxy status."""
        try:
            # Get AgentCore status
            response = await self.client.get(f"{self.agentcore_url}/status")
            if response.status_code == 200:
                agentcore_status = response.json()
                
                return {
                    "status": "healthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "AgentCore Backend Proxy",
                    "agentcore_status": agentcore_status
                }
            else:
                return {
                    "status": "unhealthy",
                    "timestamp": datetime.now().isoformat(),
                    "service": "AgentCore Backend Proxy",
                    "error": f"AgentCore status check failed: {response.status_code}"
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "service": "AgentCore Backend Proxy",
                "error": str(e)
            }

# Create the proxy instance
proxy = AgentCoreBackendProxy()

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting AgentCore Backend Proxy on port 5001...")
    uvicorn.run(proxy.app, host="0.0.0.0", port=5001, log_level="info")
