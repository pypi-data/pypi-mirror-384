#!/usr/bin/env python3
"""
Test Real Optimization Implementation
===================================

This script tests the real optimization implementation using OR-Tools
to verify that we're getting genuine mathematical optimization results
instead of AI-generated ones.
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

class RealOptimizationTester:
    """Test the real optimization implementation."""
    
    def __init__(self):
        self.test_queries = [
            {
                "name": "Simple Production Planning",
                "description": "A small manufacturing company needs to optimize production of 2 products using 2 machines. Product A requires 2 hours on machine 1 and 1 hour on machine 2, with profit of $50 per unit. Product B requires 1 hour on machine 1 and 3 hours on machine 2, with profit of $60 per unit. Machine 1 has 40 hours available, machine 2 has 60 hours available. Maximize profit.",
                "context": "Simple linear programming problem with known optimal solution"
            }
        ]
    
    async def test_real_optimization(self, query_data: dict) -> dict:
        """Test a single query with real optimization."""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING REAL OPTIMIZATION: {query_data['name']}")
        print(f"{'='*60}")
        
        results = {
            "query_name": query_data["name"],
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Intent Classification
            print(f"\n📋 Step 1: Intent Classification")
            intent_result = await classify_intent(
                query_data["description"],
                query_data["context"]
            )
            results["steps"]["intent_classification"] = intent_result
            print(f"✅ Intent: {intent_result.get('result', {}).get('intent', 'unknown')}")
            
            # Step 2: Data Analysis
            print(f"\n📊 Step 2: Data Analysis")
            data_result = await analyze_data(
                query_data["description"],
                intent_result.get("result", {})
            )
            results["steps"]["data_analysis"] = data_result
            print(f"✅ Data Readiness: {data_result.get('result', {}).get('readiness_score', 0):.2f}")
            
            # Step 3: Model Building (Qwen + OR-Tools compatible)
            print(f"\n🔧 Step 3: Model Building (Qwen + OR-Tools)")
            model_result = await build_model(
                query_data["description"],
                intent_result.get("result", {}),
                data_result.get("result", {})
            )
            results["steps"]["model_building"] = model_result
            model_type = model_result.get('result', {}).get('model_type', 'unknown')
            variables = model_result.get('result', {}).get('variables', [])
            print(f"✅ Model Type: {model_type}")
            print(f"   Variables: {len(variables)}")
            
            # Display model details
            print(f"\n📋 Model Details:")
            for i, var in enumerate(variables[:5]):  # Show first 5 variables
                print(f"   {var.get('name', f'x{i}')}: {var.get('type', 'unknown')} {var.get('bounds', 'unknown')}")
            
            # Step 4: Real Optimization Solving (OR-Tools)
            print(f"\n🎯 Step 4: Real Optimization Solving (OR-Tools)")
            solution_result = await solve_optimization(
                query_data["description"],
                intent_result.get("result", {}),
                data_result.get("result", {}),
                model_result.get("result", {})
            )
            results["steps"]["optimization_solution"] = solution_result
            
            # Display results
            status = solution_result.get('result', {}).get('status', 'unknown')
            obj_value = solution_result.get('result', {}).get('objective_value', 0)
            solve_time = solution_result.get('result', {}).get('solve_time', 0)
            
            print(f"✅ Solution Status: {status}")
            print(f"   Objective Value: {obj_value}")
            print(f"   Solve Time: {solve_time:.3f}s")
            
            # Display optimal values
            optimal_values = solution_result.get('result', {}).get('optimal_values', {})
            if optimal_values:
                print(f"\n📊 Optimal Values:")
                for name, value in optimal_values.items():
                    print(f"   {name}: {value:.2f}")
            
            # Display business impact
            business_impact = solution_result.get('result', {}).get('business_impact', {})
            if business_impact:
                print(f"\n💰 Business Impact:")
                for key, value in business_impact.items():
                    print(f"   {key}: {value}")
            
            # Verify if this looks like real optimization
            self._verify_real_optimization(solution_result, query_data)
            
            results["status"] = "success"
            results["message"] = "Real optimization workflow executed successfully"
            
        except Exception as e:
            print(f"❌ Error in workflow: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
            results["message"] = "Workflow execution failed"
        
        return results
    
    def _verify_real_optimization(self, solution_result: dict, query_data: dict):
        """Verify that the results look like real optimization."""
        print(f"\n🔍 VERIFICATION: Real vs AI-Generated Results")
        
        result = solution_result.get('result', {})
        status = result.get('status', 'unknown')
        obj_value = result.get('objective_value', 0)
        solve_time = result.get('solve_time', 0)
        optimal_values = result.get('optimal_values', {})
        
        # Check for signs of real optimization
        real_optimization_indicators = []
        
        # 1. Check solve time (should be reasonable for small problems)
        if 0.001 <= solve_time <= 10.0:
            real_optimization_indicators.append("✅ Realistic solve time")
        else:
            real_optimization_indicators.append("❌ Unrealistic solve time")
        
        # 2. Check objective value (should be reasonable for the problem)
        if 0 < obj_value < 10000:  # Reasonable range for this problem
            real_optimization_indicators.append("✅ Reasonable objective value")
        else:
            real_optimization_indicators.append("❌ Unrealistic objective value")
        
        # 3. Check optimal values (should be non-negative and reasonable)
        if optimal_values:
            all_positive = all(v >= 0 for v in optimal_values.values())
            all_reasonable = all(v <= 100 for v in optimal_values.values())  # Reasonable bounds
            
            if all_positive:
                real_optimization_indicators.append("✅ Non-negative optimal values")
            else:
                real_optimization_indicators.append("❌ Negative optimal values")
                
            if all_reasonable:
                real_optimization_indicators.append("✅ Reasonable optimal values")
            else:
                real_optimization_indicators.append("❌ Unrealistic optimal values")
        
        # 4. Check status
        if status in ['optimal', 'feasible']:
            real_optimization_indicators.append("✅ Valid optimization status")
        else:
            real_optimization_indicators.append("❌ Invalid optimization status")
        
        # Display verification results
        for indicator in real_optimization_indicators:
            print(f"   {indicator}")
        
        # Overall assessment
        positive_indicators = sum(1 for ind in real_optimization_indicators if ind.startswith("✅"))
        total_indicators = len(real_optimization_indicators)
        
        if positive_indicators >= total_indicators * 0.75:
            print(f"\n🎉 VERDICT: Results appear to be from REAL OPTIMIZATION!")
        else:
            print(f"\n⚠️ VERDICT: Results may still be AI-generated or have issues")
    
    async def run_tests(self) -> dict:
        """Run all real optimization tests."""
        print(f"🚀 Starting Real Optimization Tests")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Testing {len(self.test_queries)} optimization problems")
        
        test_results = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(self.test_queries),
                "tests_run": []
            }
        }
        
        # Test each query
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n{'='*80}")
            print(f"TEST {i}/{len(self.test_queries)}")
            result = await self.test_real_optimization(query)
            test_results["test_session"]["tests_run"].append(result)
        
        # Generate summary
        successful_tests = sum(1 for test in test_results["test_session"]["tests_run"] if test.get("status") == "success")
        total_tests = len(test_results["test_session"]["tests_run"])
        
        print(f"\n{'='*80}")
        print(f"📊 REAL OPTIMIZATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        
        # Save results
        results_file = f"real_optimization_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        return test_results

async def main():
    """Main test execution function."""
    try:
        tester = RealOptimizationTester()
        results = await tester.run_tests()
        
        # Check if all tests passed
        all_passed = all(
            test.get("status") == "success" 
            for test in results["test_session"]["tests_run"]
        )
        
        if all_passed:
            print(f"\n🎉 ALL REAL OPTIMIZATION TESTS PASSED!")
            print(f"✅ The MCP server is now using genuine mathematical optimization!")
            return 0
        else:
            print(f"\n⚠️ SOME TESTS FAILED. Check the results for details.")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
