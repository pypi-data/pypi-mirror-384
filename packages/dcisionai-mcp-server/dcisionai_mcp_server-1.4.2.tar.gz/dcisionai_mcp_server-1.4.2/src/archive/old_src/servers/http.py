#!/usr/bin/env python3
"""
Simple HTTP Server for DcisionAI Manufacturing MCP Server
========================================================

A basic HTTP server that exposes the MCP tools as REST endpoints.
This is a fallback when FastMCP has issues.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mcp_server import SimplifiedManufacturingTools, manufacturing_health_check, manufacturing_optimize

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Initialize the manufacturing tools
tools = SimplifiedManufacturingTools()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test the tools
        health_result = manufacturing_health_check()
        return jsonify({
            "status": "healthy",
            "version": health_result.get("version", "1.0.0"),
            "architecture": health_result.get("architecture", "4-agent simplified"),
            "tools_available": health_result.get("tools_available", 2),
            "bedrock_connected": health_result.get("bedrock_connected", True)
        })
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/mcp', methods=['POST'])
def handle_mcp_request():
    """Handle MCP-style requests."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        method = data.get('method', '')
        params = data.get('params', {})
        
        logger.info(f"Handling MCP request: {method}")
        
        if method == 'tools/call':
            tool_name = params.get('name', '')
            arguments = params.get('arguments', {})
            
            if tool_name == 'manufacturing_optimize':
                result = manufacturing_optimize(
                    problem_description=arguments.get('problem_description', ''),
                    constraints=arguments.get('constraints', {}),
                    optimization_goals=arguments.get('optimization_goals', [])
                )
                
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result)
                            }
                        ]
                    }
                })
                
            elif tool_name == 'manufacturing_health_check':
                result = manufacturing_health_check()
                
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result)
                            }
                        ]
                    }
                })
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": data.get('id', 1),
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}"
                    }
                }), 404
        else:
            return jsonify({
                "jsonrpc": "2.0",
                "id": data.get('id', 1),
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }), 404
            
    except Exception as e:
        logger.error(f"MCP request failed: {e}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": data.get('id', 1) if data else 1,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        }), 500

@app.route('/optimize', methods=['POST'])
def optimize_direct():
    """Direct optimization endpoint."""
    try:
        data = request.get_json()
        
        result = manufacturing_optimize(
            problem_description=data.get('problem_description', ''),
            constraints=data.get('constraints', {}),
            optimization_goals=data.get('optimization_goals', [])
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        return jsonify({
            "error": str(e),
            "status": "failed"
        }), 500

if __name__ == '__main__':
    print("🚀 Starting DcisionAI Manufacturing HTTP Server...")
    print("📡 Available endpoints:")
    print("   - GET  /health - Health check")
    print("   - POST /mcp - MCP protocol endpoint")
    print("   - POST /optimize - Direct optimization")
    print("🌐 Server will be available at: http://localhost:8000")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
