#!/usr/bin/env python3
"""
End-to-End Test for DcisionAI MCP Server
========================================

This script tests the complete optimization workflow from intent classification
to final optimization results.
"""

import asyncio
import json
import sys
import os

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from dcisionai_mcp_server.tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization,
    select_solver,
    explain_optimization
)

async def test_complete_workflow():
    """Test the complete optimization workflow."""
    
    # Real-world portfolio optimization problem
    problem_description = """
    I'm a 45-year-old executive with $2M to invest. I need to optimize my portfolio 
    across stocks, bonds, real estate, and commodities. I want to maximize returns 
    while keeping volatility under 12% and ensuring at least 20% allocation to bonds 
    for stability.
    
    Available assets:
    - Stocks: Expected return 10%, Volatility 18%
    - Bonds: Expected return 4%, Volatility 6%  
    - Real Estate: Expected return 8%, Volatility 15%
    - Commodities: Expected return 6%, Volatility 20%
    
    Constraints:
    - Maximum 12% portfolio volatility
    - Minimum 20% allocation to bonds
    - All allocations must sum to 100%
    """
    
    print("🚀 Starting End-to-End DcisionAI MCP Server Test")
    print("=" * 60)
    
    try:
        # Step 1: Intent Classification
        print("\n📋 Step 1: Intent Classification")
        print("-" * 30)
        intent_result = await classify_intent(problem_description)
        print(f"✅ Intent: {intent_result['result']['intent']}")
        print(f"✅ Industry: {intent_result['result']['industry']}")
        print(f"✅ Optimization Type: {intent_result['result']['optimization_type']}")
        print(f"✅ Confidence: {intent_result['result']['confidence']}")
        
        # Step 2: Data Analysis
        print("\n📊 Step 2: Data Analysis")
        print("-" * 30)
        data_result = await analyze_data(problem_description, intent_result['result'])
        print(f"✅ Data Readiness: {data_result['result']['readiness_score']}")
        print(f"✅ Variables Identified: {len(data_result['result']['variables_identified'])}")
        print(f"✅ Constraints Identified: {len(data_result['result']['constraints_identified'])}")
        
        # Step 3: Solver Selection
        print("\n🔧 Step 3: Solver Selection")
        print("-" * 30)
        solver_result = await select_solver(
            intent_result['result']['optimization_type'],
            {"num_variables": 4, "num_constraints": 3},
            "balanced"
        )
        print(f"✅ Selected Solver: {solver_result['result']['selected_solver']}")
        print(f"✅ Performance Rating: {solver_result['result']['performance_rating']}/10")
        print(f"✅ Available Solvers: {len(solver_result['result']['available_solvers'])}")
        
        # Step 4: Model Building
        print("\n🏗️ Step 4: Model Building")
        print("-" * 30)
        model_result = await build_model(problem_description, intent_result['result'], data_result['result'])
        print(f"✅ Model Type: {model_result['result']['model_type']}")
        print(f"✅ Variables: {len(model_result['result']['variables'])}")
        print(f"✅ Constraints: {len(model_result['result']['constraints'])}")
        print(f"✅ Objective: {model_result['result']['objective']['type']}")
        
        # Step 5: Optimization Solving
        print("\n⚡ Step 5: Optimization Solving")
        print("-" * 30)
        optimization_result = await solve_optimization(
            problem_description, 
            intent_result['result'], 
            data_result['result'], 
            model_result['result']
        )
        print(f"✅ Status: {optimization_result['result']['status']}")
        print(f"✅ Objective Value: {optimization_result['result']['objective_value']}")
        print(f"✅ Solve Time: {optimization_result['result']['solve_time']} seconds")
        
        # Display optimal allocation
        if 'variables' in optimization_result['result']:
            print("\n📈 Optimal Portfolio Allocation:")
            for var in optimization_result['result']['variables']:
                if 'value' in var:
                    print(f"   {var['name']}: {var['value']:.1%}")
        
        # Step 6: Business Explainability
        print("\n💡 Step 6: Business Explainability")
        print("-" * 30)
        explain_result = await explain_optimization(
            problem_description,
            intent_result['result'],
            data_result['result'],
            model_result['result'],
            optimization_result['result']
        )
        print(f"✅ Executive Summary Generated")
        print(f"✅ Analysis Breakdown: {len(explain_result['result']['analysis_breakdown'])} sections")
        print(f"✅ Implementation Guidance: {len(explain_result['result']['implementation_guidance']['next_steps'])} steps")
        
        print("\n🎉 End-to-End Test Completed Successfully!")
        print("=" * 60)
        
        # Summary
        print("\n📋 Test Summary:")
        print(f"✅ Intent Classification: {intent_result['status']}")
        print(f"✅ Data Analysis: {data_result['status']}")
        print(f"✅ Solver Selection: {solver_result['status']}")
        print(f"✅ Model Building: {model_result['status']}")
        print(f"✅ Optimization Solving: {optimization_result['status']}")
        print(f"✅ Business Explainability: {explain_result['status']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test Failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_complete_workflow())
    sys.exit(0 if success else 1)
