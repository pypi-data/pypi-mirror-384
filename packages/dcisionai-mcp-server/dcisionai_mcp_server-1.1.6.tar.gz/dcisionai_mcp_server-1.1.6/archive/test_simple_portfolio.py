#!/usr/bin/env python3
"""
Simple Portfolio Optimization Test
=================================

A simpler portfolio optimization test to avoid segmentation faults
while still testing complex optimization capabilities.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dcisionai_mcp_server.tools import (
    classify_intent,
    analyze_data,
    build_model,
    solve_optimization
)

async def test_simple_portfolio():
    """Test a simple but realistic portfolio optimization."""
    
    query = {
        "name": "Simple Portfolio Optimization",
        "description": """A financial advisor needs to optimize a portfolio of 5 stocks for a client with $1 million to invest.

STOCKS:
- AAPL (Apple): Expected return 12%, Risk 20%
- MSFT (Microsoft): Expected return 10%, Risk 18%  
- GOOGL (Google): Expected return 11%, Risk 22%
- JNJ (Johnson & Johnson): Expected return 8%, Risk 15%
- JPM (JPMorgan): Expected return 9%, Risk 16%

CONSTRAINTS:
1. Maximum 30% allocation to any single stock
2. Minimum 10% allocation to any stock if included
3. Total investment must equal exactly $1 million
4. Portfolio risk must not exceed 18% annually
5. Maximum 4 stocks can be included

OBJECTIVE: Maximize expected portfolio return while keeping risk under 18%.""",
        "context": "Simple portfolio optimization with risk constraints"
    }
    
    print(f"🧪 TESTING SIMPLE PORTFOLIO OPTIMIZATION")
    print(f"{'='*60}")
    
    try:
        # Step 1: Intent Classification
        print(f"\n📋 Step 1: Intent Classification")
        intent_result = await classify_intent(query["description"], query["context"])
        print(f"✅ Intent: {intent_result.get('result', {}).get('intent', 'unknown')}")
        print(f"   Industry: {intent_result.get('result', {}).get('industry', 'unknown')}")
        print(f"   Complexity: {intent_result.get('result', {}).get('complexity', 'unknown')}")
        
        # Step 2: Data Analysis
        print(f"\n📊 Step 2: Data Analysis")
        data_result = await analyze_data(query["description"], intent_result.get("result", {}))
        print(f"✅ Data Readiness: {data_result.get('result', {}).get('readiness_score', 0):.2f}")
        print(f"   Entities: {data_result.get('result', {}).get('entities', 0)}")
        
        # Step 3: Model Building
        print(f"\n🔧 Step 3: Model Building")
        model_result = await build_model(
            query["description"],
            intent_result.get("result", {}),
            data_result.get("result", {})
        )
        variables = model_result.get('result', {}).get('variables', [])
        constraints = model_result.get('result', {}).get('constraints', [])
        print(f"✅ Model Type: {model_result.get('result', {}).get('model_type', 'unknown')}")
        print(f"   Variables: {len(variables)}")
        print(f"   Constraints: {len(constraints)}")
        
        # Step 4: Optimization Solving
        print(f"\n🎯 Step 4: Real Optimization Solving")
        solution_result = await solve_optimization(
            query["description"],
            intent_result.get("result", {}),
            data_result.get("result", {}),
            model_result.get("result", {})
        )
        
        status = solution_result.get('result', {}).get('status', 'unknown')
        obj_value = solution_result.get('result', {}).get('objective_value', 0)
        solve_time = solution_result.get('result', {}).get('solve_time', 0)
        
        print(f"✅ Solution Status: {status}")
        print(f"   Objective Value: {obj_value}")
        print(f"   Solve Time: {solve_time:.3f}s")
        
        # Display results
        optimal_values = solution_result.get('result', {}).get('optimal_values', {})
        if optimal_values:
            print(f"\n📊 Optimal Portfolio:")
            total = 0
            for name, value in optimal_values.items():
                if isinstance(value, (int, float)) and value > 0:
                    print(f"   {name}: {value:.3f}")
                    total += value
            print(f"   Total: {total:.3f}")
        
        # Save results
        results = {
            "test_name": "Simple Portfolio Optimization",
            "timestamp": datetime.now().isoformat(),
            "intent_classification": intent_result,
            "data_analysis": data_result,
            "model_building": model_result,
            "optimization_solution": solution_result
        }
        
        results_file = f"simple_portfolio_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        return results_file
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None

if __name__ == "__main__":
    results_file = asyncio.run(test_simple_portfolio())
    if results_file:
        print(f"\n✅ Test completed successfully!")
        print(f"📄 Results file: {results_file}")
    else:
        print(f"\n❌ Test failed!")
        sys.exit(1)
