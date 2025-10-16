#!/usr/bin/env python3
"""
Debug MCP Server - Log all communication
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict

# Configure logging to file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/mcp_debug.log'),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

def main():
    """Debug MCP server that logs everything."""
    logger.info("Starting debug MCP server")
    
    # Read from stdin and write to stdout directly
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            
            logger.info(f"Received raw line: {repr(line)}")
            
            # Parse JSON-RPC message
            try:
                message = json.loads(line.strip())
                logger.info(f"Parsed message: {json.dumps(message, indent=2)}")
                
                method = message.get("method")
                logger.info(f"Method: {method}")
                
                if method == "initialize":
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {
                                "tools": {}
                            },
                            "serverInfo": {
                                "name": "debug-server",
                                "version": "1.0.0"
                            }
                        }
                    }
                    logger.info(f"Sending response: {json.dumps(response, indent=2)}")
                    print(json.dumps(response))
                    sys.stdout.flush()
                
                elif method == "tools/list":
                    response = {
                        "jsonrpc": "2.0",
                        "id": message.get("id"),
                        "result": {
                            "tools": [
                                {
                                    "name": "test_tool",
                                    "description": "A test tool",
                                    "inputSchema": {
                                        "type": "object",
                                        "properties": {
                                            "message": {
                                                "type": "string",
                                                "description": "Test message"
                                            }
                                        },
                                        "required": ["message"]
                                    }
                                }
                            ]
                        }
                    }
                    logger.info(f"Sending tools response: {json.dumps(response, indent=2)}")
                    print(json.dumps(response))
                    sys.stdout.flush()
                
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
                    print(json.dumps(response))
                    sys.stdout.flush()
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                continue
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            break

if __name__ == "__main__":
    main()
