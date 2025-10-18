#!/usr/bin/env python3
"""
Test client for Bedrock AgentCore MCP Server
Based on AWS Bedrock AgentCore documentation
"""

import asyncio
import os
import sys
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    # Get the agent ARN from environment or use the deployed one
    agent_arn = "arn:aws:bedrock-agentcore:us-east-1:808953421331:runtime/bedrock_agentcore_mcp_server-uZ4MxJ2bNZ"
    
    # For Bedrock AgentCore, we need to use the invoke endpoint
    encoded_arn = agent_arn.replace(':', '%3A').replace('/', '%2F')
    mcp_url = f"https://bedrock-agentcore.us-east-1.amazonaws.com/runtimes/{encoded_arn}/invocations?qualifier=DEFAULT"
    
    # For IAM authentication, we don't need bearer token
    headers = {"Content-Type": "application/json"}
    
    print(f"Invoking: {mcp_url}")
    print(f"With headers: {headers}")
    print()

    try:
        async with streamablehttp_client(mcp_url, headers, timeout=120, terminate_on_close=False) as (
            read_stream,
            write_stream,
            _,
        ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                
                # List available tools
                print("🔧 Listing available tools...")
                tool_result = await session.list_tools()
                print("Available tools:", tool_result)
                print()
                
                # Test health check
                print("🏥 Testing health check...")
                health_result = await session.call_tool("manufacturing_health_check", {})
                print("Health check result:", health_result)
                print()
                
                # Test optimization
                print("🚀 Testing optimization...")
                opt_result = await session.call_tool("manufacturing_optimize", {
                    "problem_description": "Optimize production line efficiency with 50 workers across 3 manufacturing lines",
                    "constraints": {},
                    "optimization_goals": []
                })
                print("Optimization result:", opt_result)
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
