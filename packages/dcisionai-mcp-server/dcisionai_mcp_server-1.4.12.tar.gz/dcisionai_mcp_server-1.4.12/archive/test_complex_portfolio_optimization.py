#!/usr/bin/env python3
"""
Complex Portfolio Optimization Test
==================================

This script tests the MCP server with a complex portfolio optimization problem
that involves multiple assets, risk constraints, and realistic financial parameters.
This will stress-test the real optimization system.
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

class ComplexPortfolioOptimizationTester:
    """Test complex portfolio optimization with real optimization."""
    
    def __init__(self):
        self.test_queries = [
            {
                "name": "Complex Portfolio Optimization",
                "description": """A financial institution needs to optimize a portfolio of 15 different assets for a client with $10 million to invest. The portfolio must meet the following requirements:

ASSETS:
- Technology stocks: AAPL, MSFT, GOOGL, AMZN, TSLA (expected returns: 12%, 10%, 11%, 13%, 15%)
- Healthcare stocks: JNJ, PFE, UNH, ABBV, GILD (expected returns: 8%, 6%, 9%, 7%, 10%)
- Financial stocks: JPM, BAC, WFC, GS, C (expected returns: 9%, 7%, 8%, 11%, 6%)

CONSTRAINTS:
1. Maximum 40% allocation to any single sector
2. Minimum 20% allocation to each sector
3. Maximum 15% allocation to any single stock
4. Minimum 5% allocation to any stock if included
5. Portfolio volatility must not exceed 12% annually
6. Maximum 8 stocks can be included in the portfolio
7. Total investment must equal exactly $10 million

OBJECTIVE: Maximize expected portfolio return while minimizing risk (maximize Sharpe ratio approximation).

RISK PARAMETERS:
- Technology sector correlation: 0.7
- Healthcare sector correlation: 0.4
- Financial sector correlation: 0.6
- Cross-sector correlation: 0.3
- Individual stock volatilities range from 15% to 35%""",
                "context": "Complex financial portfolio optimization with multiple constraints and risk management"
            },
            {
                "name": "Multi-Period Portfolio Rebalancing",
                "description": """A pension fund needs to optimize portfolio rebalancing across 4 quarters with changing market conditions and cash flow requirements.

PORTFOLIO COMPONENTS:
- 20 different assets across 5 sectors
- Starting portfolio value: $50 million
- Quarterly cash inflows: $2M, $1.5M, $3M, $2.5M
- Quarterly liability payments: $1M, $1.2M, $1.8M, $2M

CONSTRAINTS:
1. Transaction costs: 0.1% per trade
2. Maximum 25% turnover per quarter
3. Minimum liquidity requirements: 5% in cash equivalents
4. Regulatory constraints: max 30% in any single sector
5. Risk budget: portfolio VaR must not exceed 2% monthly
6. Rebalancing frequency: quarterly
7. Tax considerations: minimize realized capital gains

OBJECTIVE: Maximize risk-adjusted returns over 4 quarters while meeting cash flow requirements and regulatory constraints.

MARKET CONDITIONS:
- Q1: Bull market, high volatility
- Q2: Bear market, moderate volatility  
- Q3: Recovery, low volatility
- Q4: Sideways, moderate volatility""",
                "context": "Multi-period portfolio optimization with dynamic rebalancing and cash flow management"
            }
        ]
    
    async def test_complex_optimization(self, query_data: dict) -> dict:
        """Test a complex optimization query."""
        print(f"\n{'='*80}")
        print(f"🧪 TESTING COMPLEX OPTIMIZATION: {query_data['name']}")
        print(f"{'='*80}")
        
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
            print(f"   Industry: {intent_result.get('result', {}).get('industry', 'unknown')}")
            print(f"   Complexity: {intent_result.get('result', {}).get('complexity', 'unknown')}")
            
            # Step 2: Data Analysis
            print(f"\n📊 Step 2: Data Analysis")
            data_result = await analyze_data(
                query_data["description"],
                intent_result.get("result", {})
            )
            results["steps"]["data_analysis"] = data_result
            readiness = data_result.get('result', {}).get('readiness_score', 0)
            entities = data_result.get('result', {}).get('entities', 0)
            print(f"✅ Data Readiness: {readiness:.2f}")
            print(f"   Entities: {entities}")
            print(f"   Quality: {data_result.get('result', {}).get('data_quality', 'unknown')}")
            
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
            constraints = model_result.get('result', {}).get('constraints', [])
            print(f"✅ Model Type: {model_type}")
            print(f"   Variables: {len(variables)}")
            print(f"   Constraints: {len(constraints)}")
            
            # Display model complexity
            print(f"\n📋 Model Complexity Analysis:")
            print(f"   Variables by type:")
            var_types = {}
            for var in variables:
                var_type = var.get('type', 'unknown')
                var_types[var_type] = var_types.get(var_type, 0) + 1
            for vtype, count in var_types.items():
                print(f"     {vtype}: {count}")
            
            print(f"   Constraint types:")
            constraint_types = {}
            for constraint in constraints:
                desc = constraint.get('description', '').lower()
                if 'allocation' in desc or 'percentage' in desc:
                    constraint_types['allocation'] = constraint_types.get('allocation', 0) + 1
                elif 'risk' in desc or 'volatility' in desc:
                    constraint_types['risk'] = constraint_types.get('risk', 0) + 1
                elif 'budget' in desc or 'cost' in desc:
                    constraint_types['budget'] = constraint_types.get('budget', 0) + 1
                else:
                    constraint_types['other'] = constraint_types.get('other', 0) + 1
            for ctype, count in constraint_types.items():
                print(f"     {ctype}: {count}")
            
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
                print(f"\n📊 Optimal Portfolio Allocation:")
                total_allocation = 0
                for name, value in optimal_values.items():
                    if isinstance(value, (int, float)) and value > 0:
                        print(f"   {name}: {value:.2f}")
                        total_allocation += value
                print(f"   Total Allocation: {total_allocation:.2f}")
            
            # Display business impact
            business_impact = solution_result.get('result', {}).get('business_impact', {})
            if business_impact:
                print(f"\n💰 Portfolio Performance:")
                for key, value in business_impact.items():
                    print(f"   {key}: {value}")
            
            # Verify complexity and realism
            self._verify_complex_optimization(solution_result, query_data, model_result)
            
            results["status"] = "success"
            results["message"] = "Complex optimization workflow executed successfully"
            
        except Exception as e:
            print(f"❌ Error in workflow: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
            results["message"] = "Workflow execution failed"
        
        return results
    
    def _verify_complex_optimization(self, solution_result: dict, query_data: dict, model_result: dict):
        """Verify that the complex optimization results are realistic."""
        print(f"\n🔍 COMPLEX OPTIMIZATION VERIFICATION")
        
        result = solution_result.get('result', {})
        status = result.get('status', 'unknown')
        obj_value = result.get('objective_value', 0)
        solve_time = result.get('solve_time', 0)
        optimal_values = result.get('optimal_values', {})
        
        # Check for signs of real complex optimization
        complexity_indicators = []
        
        # 1. Check model complexity
        variables = model_result.get('result', {}).get('variables', [])
        constraints = model_result.get('result', {}).get('constraints', [])
        
        if len(variables) >= 10:
            complexity_indicators.append("✅ High variable count (complex model)")
        else:
            complexity_indicators.append("⚠️ Low variable count for complex problem")
        
        if len(constraints) >= 8:
            complexity_indicators.append("✅ High constraint count (realistic complexity)")
        else:
            complexity_indicators.append("⚠️ Low constraint count for complex problem")
        
        # 2. Check solve time (should be longer for complex problems)
        if 0.01 <= solve_time <= 5.0:
            complexity_indicators.append("✅ Realistic solve time for complex problem")
        elif solve_time < 0.01:
            complexity_indicators.append("⚠️ Suspiciously fast solve time for complex problem")
        else:
            complexity_indicators.append("⚠️ Suspiciously slow solve time")
        
        # 3. Check objective value realism
        if 0 < obj_value < 1000000:  # Reasonable range for portfolio optimization
            complexity_indicators.append("✅ Realistic objective value")
        else:
            complexity_indicators.append("❌ Unrealistic objective value")
        
        # 4. Check solution diversity (should have multiple non-zero allocations)
        non_zero_values = [v for v in optimal_values.values() if isinstance(v, (int, float)) and v > 0.01]
        if len(non_zero_values) >= 3:
            complexity_indicators.append("✅ Diversified portfolio allocation")
        else:
            complexity_indicators.append("⚠️ Low portfolio diversification")
        
        # 5. Check for realistic portfolio constraints
        total_allocation = sum(v for v in optimal_values.values() if isinstance(v, (int, float)))
        if 0.95 <= total_allocation <= 1.05:  # Should be close to 100%
            complexity_indicators.append("✅ Realistic total allocation (~100%)")
        else:
            complexity_indicators.append("⚠️ Unrealistic total allocation")
        
        # Display verification results
        for indicator in complexity_indicators:
            print(f"   {indicator}")
        
        # Overall assessment
        positive_indicators = sum(1 for ind in complexity_indicators if ind.startswith("✅"))
        total_indicators = len(complexity_indicators)
        
        if positive_indicators >= total_indicators * 0.8:
            print(f"\n🎉 VERDICT: Complex optimization appears to be REAL and REALISTIC!")
        elif positive_indicators >= total_indicators * 0.6:
            print(f"\n⚠️ VERDICT: Complex optimization shows some concerns but may be legitimate.")
        else:
            print(f"\n❌ VERDICT: Complex optimization results appear suspicious.")
    
    async def run_complex_tests(self) -> dict:
        """Run all complex optimization tests."""
        print(f"🚀 Starting Complex Portfolio Optimization Tests")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Testing {len(self.test_queries)} complex optimization problems")
        
        test_results = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(self.test_queries),
                "tests_run": []
            }
        }
        
        # Test each complex query
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n{'='*100}")
            print(f"COMPLEX TEST {i}/{len(self.test_queries)}")
            result = await self.test_complex_optimization(query)
            test_results["test_session"]["tests_run"].append(result)
        
        # Generate summary
        successful_tests = sum(1 for test in test_results["test_session"]["tests_run"] if test.get("status") == "success")
        total_tests = len(test_results["test_session"]["tests_run"])
        
        print(f"\n{'='*100}")
        print(f"📊 COMPLEX OPTIMIZATION TEST SUMMARY")
        print(f"{'='*100}")
        print(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        
        # Calculate complexity metrics
        total_variables = 0
        total_constraints = 0
        total_solve_time = 0
        
        for test in test_results["test_session"]["tests_run"]:
            if test.get("status") == "success":
                model_result = test["steps"]["model_building"]["result"]
                solution_result = test["steps"]["optimization_solution"]["result"]
                
                total_variables += len(model_result.get("variables", []))
                total_constraints += len(model_result.get("constraints", []))
                total_solve_time += solution_result.get("solve_time", 0)
        
        if successful_tests > 0:
            avg_variables = total_variables / successful_tests
            avg_constraints = total_constraints / successful_tests
            avg_solve_time = total_solve_time / successful_tests
            
            print(f"📈 Complexity Metrics:")
            print(f"   Average Variables: {avg_variables:.1f}")
            print(f"   Average Constraints: {avg_constraints:.1f}")
            print(f"   Average Solve Time: {avg_solve_time:.3f}s")
        
        # Save results
        results_file = f"complex_portfolio_optimization_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        return test_results, results_file

async def main():
    """Main test execution function."""
    try:
        tester = ComplexPortfolioOptimizationTester()
        test_results, results_file = await tester.run_complex_tests()
        
        # Check if all tests passed
        all_passed = all(
            test.get("status") == "success" 
            for test in test_results["test_session"]["tests_run"]
        )
        
        if all_passed:
            print(f"\n🎉 ALL COMPLEX OPTIMIZATION TESTS PASSED!")
            print(f"✅ The MCP server successfully handles complex portfolio optimization!")
            return 0, results_file
        else:
            print(f"\n⚠️ SOME TESTS FAILED. Check the results for details.")
            return 1, results_file
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1, None

if __name__ == "__main__":
    exit_code, results_file = asyncio.run(main())
    if results_file:
        print(f"\n📄 Results file: {results_file}")
    sys.exit(exit_code)
