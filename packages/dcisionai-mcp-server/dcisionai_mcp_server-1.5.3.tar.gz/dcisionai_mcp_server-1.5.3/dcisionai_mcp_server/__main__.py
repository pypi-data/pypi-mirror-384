#!/usr/bin/env python3
"""
DcisionAI MCP Server - Main Entry Point
=======================================

This is the main entry point for the DcisionAI MCP Server when run as a module.
It provides the standard MCP protocol implementation for Cursor IDE integration.
"""

import asyncio
import sys
from .mcp_server import main

if __name__ == "__main__":
    asyncio.run(main())
