"""
DcisionAI MCP Server - Optimization Intelligence for AI Workflows

This package provides optimization capabilities through the Model Context Protocol (MCP),
enabling AI agents to solve complex optimization problems across multiple industries.

Key Features:
- 7 Industry Workflows: Manufacturing, Healthcare, Retail, Marketing, Financial, Logistics, Energy
- Qwen 30B Integration: Advanced mathematical optimization
- Real-Time Results: Actual optimization solutions with mathematical proofs
- MCP Protocol: Seamless integration with AI development environments

Example Usage:
    from dcisionai_mcp_server import mcp
    
    # Execute a manufacturing optimization workflow
    result = mcp.execute_workflow(
        industry="manufacturing",
        workflow_id="production_planning"
    )
"""

__version__ = "1.0.0"
__author__ = "DcisionAI"
__email__ = "contact@dcisionai.com"
__description__ = "Optimization Intelligence for AI Workflows via Model Context Protocol (MCP)"

# Import main components (lazy loading to avoid config validation on import)
try:
    from .mcp_server import DcisionAIMCPServer, main as run_server
    from .tools import (
        classify_intent,
        analyze_data,
        build_model,
        solve_optimization,
        select_solver,
        explain_optimization,
        get_workflow_templates,
        execute_workflow
    )
except Exception as e:
    # If import fails due to missing config, provide helpful error
    import warnings
    warnings.warn(f"Some components could not be imported: {e}. Make sure to configure the MCP server properly.")
    
    # Provide None values for failed imports
    DcisionAIMCPServer = None
    run_server = None
    classify_intent = None
    analyze_data = None
    build_model = None
    solve_optimization = None
    select_solver = None
    explain_optimization = None
    get_workflow_templates = None
    execute_workflow = None

# Export main components
__all__ = [
    "DcisionAIMCPServer",
    "run_server",
    "classify_intent",
    "analyze_data", 
    "build_model",
    "solve_optimization",
    "select_solver",
    "explain_optimization",
    "get_workflow_templates",
    "execute_workflow"
]