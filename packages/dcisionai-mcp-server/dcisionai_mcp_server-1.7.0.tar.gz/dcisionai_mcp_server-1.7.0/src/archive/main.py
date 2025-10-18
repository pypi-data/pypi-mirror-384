#!/usr/bin/env python3
"""
DcisionAI Manufacturing MCP Server - Main Entry Point
====================================================

This is the main entry point for the DcisionAI Manufacturing MCP Server.
It imports and runs the MCP server from the organized src/ directory.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the MCP server
if __name__ == "__main__":
    from src.mcp_server import mcp
    print("🚀 Starting DcisionAI Manufacturing MCP Server...")
    print("📁 Using organized source structure from src/")
    mcp.run()
