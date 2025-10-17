#!/usr/bin/env python3
"""
DcisionAI MCP Server CLI
========================

Command-line interface for the DcisionAI MCP server.
Provides easy server management and testing capabilities.
"""

import asyncio
import argparse
import logging
import sys
from typing import Optional
from .mcp_server import DcisionAIMCPServer
from .config import Config, get_config
from .workflows import WorkflowManager

def setup_logging(level: str = "INFO"):
    """Set up logging configuration."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

async def run_server(host: str, port: int, config: Optional[Config] = None):
    """Run the MCP server."""
    server = DcisionAIMCPServer(config)
    await server.run()

def list_workflows():
    """List all available workflows."""
    manager = WorkflowManager()
    workflows = manager.get_all_workflows()
    
    print("DcisionAI Available Workflows")
    print("=" * 50)
    print(f"Total Industries: {workflows['total_industries']}")
    print(f"Total Workflows: {workflows['total_workflows']}")
    print()
    
    for industry, industry_workflows in workflows['workflows'].items():
        print(f"📁 {industry.title()}")
        for workflow_id, workflow in industry_workflows.items():
            print(f"  • {workflow['name']}")
            print(f"    ID: {workflow_id}")
            print(f"    Complexity: {workflow['complexity']}")
            print(f"    Time: {workflow['estimated_time']}")
            print()

def show_workflow_details(industry: str, workflow_id: str):
    """Show detailed information about a specific workflow."""
    manager = WorkflowManager()
    details = manager.get_workflow_details(industry, workflow_id)
    
    if "error" in details:
        print(f"❌ Error: {details['error']}")
        return
    
    print(f"Workflow Details: {details['name']}")
    print("=" * 50)
    print(f"Industry: {details['industry']}")
    print(f"Workflow ID: {details['workflow_id']}")
    print(f"Description: {details['description']}")
    print(f"Complexity: {details['complexity']}")
    print(f"Estimated Time: {details['estimated_time']}")
    print(f"Workflows: {details['workflows']}")

def search_workflows(query: str):
    """Search workflows by query."""
    manager = WorkflowManager()
    results = manager.search_workflows(query)
    
    if not results:
        print(f"No workflows found for query: '{query}'")
        return
    
    print(f"Search Results for: '{query}'")
    print("=" * 50)
    for result in results:
        print(f"📁 {result['industry'].title()}")
        print(f"  • {result['name']}")
        print(f"    ID: {result['workflow_id']}")
        print(f"    Complexity: {result['complexity']}")
        print(f"    Description: {result['description']}")
        print()

def show_statistics():
    """Show workflow statistics."""
    manager = WorkflowManager()
    stats = manager.get_workflow_statistics()
    
    print("DcisionAI Workflow Statistics")
    print("=" * 50)
    print(f"Total Workflows: {stats['total_workflows']}")
    print(f"Total Industries: {stats['total_industries']}")
    print()
    print("Complexity Distribution:")
    for complexity, count in stats['complexity_distribution'].items():
        print(f"  {complexity.title()}: {count}")
    print()
    print("Industries:")
    for industry in stats['industries']:
        print(f"  • {industry.title()}")

def test_connection(config: Optional[Config] = None):
    """Test connection to AgentCore Gateway."""
    import httpx
    
    config = config or Config()
    
    print("Testing AgentCore Gateway Connection")
    print("=" * 50)
    print(f"Gateway URL: {config.gateway_url}")
    print(f"Gateway Target: {config.gateway_target}")
    print()
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.post(
                f"{config.gateway_url}/mcp",
                headers=config.get_headers(),
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": f"{config.gateway_target}___get_workflow_templates",
                        "arguments": {}
                    }
                }
            )
            
            if response.status_code == 200:
                print("✅ Connection successful!")
                print(f"Status Code: {response.status_code}")
                print("Response received from AgentCore Gateway")
            else:
                print(f"❌ Connection failed!")
                print(f"Status Code: {response.status_code}")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Connection error: {e}")

def health_check(config: Optional[Config] = None):
    """Comprehensive health check of the MCP server."""
    print("🔍 DcisionAI MCP Server Health Check")
    print("=" * 40)
    
    try:
        config = config or Config()
        
        # Test configuration
        print("📋 Testing configuration...")
        if not config.gateway_url:
            print("❌ Gateway URL not configured")
            return False
        if not config.access_token:
            print("❌ Access token not configured")
            return False
        print("✅ Configuration valid")
        
        # Test AWS credentials
        print("🔑 Testing AWS credentials...")
        try:
            import boto3
            sts = boto3.client('sts')
            sts.get_caller_identity()
            print("✅ AWS credentials valid")
        except Exception as e:
            print(f"❌ AWS credentials error: {e}")
            return False
        
        # Test AgentCore Gateway connection
        print("🌐 Testing AgentCore Gateway connection...")
        try:
            import httpx
            response = httpx.post(
                f"{config.gateway_url}/mcp",
                headers=config.get_headers(),
                json={"method": "ping"},
                timeout=10.0
            )
            if response.status_code == 200:
                print("✅ AgentCore Gateway connection successful")
            else:
                print(f"❌ AgentCore Gateway error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ AgentCore Gateway connection error: {e}")
            return False
        
        # Test workflow templates
        print("📚 Testing workflow templates...")
        try:
            manager = WorkflowManager()
            workflows = manager.get_all_workflows()
            if workflows['total_workflows'] > 0:
                print(f"✅ Workflow templates loaded: {workflows['total_workflows']} workflows")
            else:
                print("❌ No workflow templates found")
                return False
        except Exception as e:
            print(f"❌ Workflow templates error: {e}")
            return False
        
        print()
        print("🎉 All health checks passed! MCP Server is ready.")
        return True
        
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="DcisionAI MCP Server - AI-powered business optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start the server
  dcisionai-mcp-server start --host 0.0.0.0 --port 8000
  
  # List all workflows
  dcisionai-mcp-server list-workflows
  
  # Show workflow details
  dcisionai-mcp-server show-workflow manufacturing production_planning
  
  # Search workflows
  dcisionai-mcp-server search "optimization"
  
  # Test connection
  dcisionai-mcp-server test-connection
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start server command
    start_parser = subparsers.add_parser("start", help="Start the MCP server")
    start_parser.add_argument("--host", default="localhost", help="Host to bind to")
    start_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    start_parser.add_argument("--config", help="Path to configuration file")
    start_parser.add_argument("--env", choices=["development", "production", "testing"], 
                            default="development", help="Environment")
    start_parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                            default="INFO", help="Log level")
    
    # List workflows command
    subparsers.add_parser("list-workflows", help="List all available workflows")
    
    # Show workflow command
    show_parser = subparsers.add_parser("show-workflow", help="Show workflow details")
    show_parser.add_argument("industry", help="Industry name")
    show_parser.add_argument("workflow_id", help="Workflow ID")
    
    # Search workflows command
    search_parser = subparsers.add_parser("search", help="Search workflows")
    search_parser.add_argument("query", help="Search query")
    
    # Statistics command
    subparsers.add_parser("stats", help="Show workflow statistics")
    
    # Test connection command
    test_parser = subparsers.add_parser("test-connection", help="Test AgentCore Gateway connection")
    test_parser.add_argument("--config", help="Path to configuration file")
    
    # Health check command
    health_parser = subparsers.add_parser("health-check", help="Comprehensive health check")
    health_parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Set up logging
    if args.command == "start":
        setup_logging(args.log_level)
    else:
        setup_logging("INFO")
    
    # Execute commands
    if args.command == "start":
        config = None
        if args.config:
            config = Config.from_file(args.config)
        else:
            config = get_config(args.env)
        
        print(f"Starting DcisionAI MCP Server...")
        print(f"Environment: {args.env}")
        print(f"Host: {args.host}")
        print(f"Port: {args.port}")
        print(f"Log Level: {args.log_level}")
        print()
        
        asyncio.run(run_server(args.host, args.port, config))
    
    elif args.command == "list-workflows":
        list_workflows()
    
    elif args.command == "show-workflow":
        show_workflow_details(args.industry, args.workflow_id)
    
    elif args.command == "search":
        search_workflows(args.query)
    
    elif args.command == "stats":
        show_statistics()
    
    elif args.command == "test-connection":
        config = None
        if args.config:
            config = Config.from_file(args.config)
        test_connection(config)
    
    elif args.command == "health-check":
        config = None
        if args.config:
            config = Config.from_file(args.config)
        health_check(config)

if __name__ == "__main__":
    main()
