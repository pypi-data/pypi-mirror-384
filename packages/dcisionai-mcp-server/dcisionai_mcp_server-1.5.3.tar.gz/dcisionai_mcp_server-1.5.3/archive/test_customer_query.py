#!/usr/bin/env python3
"""
Test MCP Server with Real Customer Query
========================================

This script tests the DcisionAI MCP server with a real customer optimization query.
It demonstrates the complete workflow from intent classification to optimization solution.
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
    solve_optimization,
    get_workflow_templates,
    execute_workflow
)

class CustomerQueryTester:
    """Test the MCP server with real customer queries."""
    
    def __init__(self):
        self.test_queries = [
            {
                "name": "Manufacturing Production Planning",
                "description": "A manufacturing company needs to optimize their production schedule for the next quarter. They have 3 production lines, 15 different products, and need to meet customer demand while minimizing costs and maximizing profit. They have constraints on labor hours, material availability, and machine capacity.",
                "context": "Manufacturing company with multiple production lines and product variants"
            },
            {
                "name": "Supply Chain Optimization",
                "description": "A retail company wants to optimize their supply chain network. They have 50 stores across 10 regions, 3 distribution centers, and need to minimize transportation costs while ensuring 95% service level. They need to consider demand variability, lead times, and inventory holding costs.",
                "context": "Retail company with multi-region distribution network"
            },
            {
                "name": "Healthcare Resource Allocation",
                "description": "A hospital needs to optimize staff scheduling and resource allocation for their emergency department. They have 20 nurses, 8 doctors, and need to handle varying patient loads while maintaining quality of care and minimizing overtime costs.",
                "context": "Hospital emergency department with variable patient demand"
            }
        ]
    
    async def test_single_query(self, query_data: dict) -> dict:
        """Test a single customer query through the complete workflow."""
        print(f"\n{'='*60}")
        print(f"🧪 TESTING: {query_data['name']}")
        print(f"{'='*60}")
        
        results = {
            "query_name": query_data["name"],
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }
        
        try:
            # Step 1: Intent Classification
            print(f"\n📋 Step 1: Intent Classification")
            print(f"Query: {query_data['description'][:100]}...")
            
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
            
            # Step 3: Model Building
            print(f"\n🔧 Step 3: Model Building")
            model_result = await build_model(
                query_data["description"],
                intent_result.get("result", {}),
                data_result.get("result", {})
            )
            results["steps"]["model_building"] = model_result
            model_type = model_result.get('result', {}).get('model_type', 'unknown')
            complexity = model_result.get('result', {}).get('model_complexity', 'unknown')
            print(f"✅ Model Type: {model_type}")
            print(f"   Complexity: {complexity}")
            print(f"   Variables: {len(model_result.get('result', {}).get('variables', []))}")
            
            # Step 4: Optimization Solving
            print(f"\n🎯 Step 4: Optimization Solving")
            solution_result = await solve_optimization(
                query_data["description"],
                intent_result.get("result", {}),
                data_result.get("result", {}),
                model_result.get("result", {})
            )
            results["steps"]["optimization_solution"] = solution_result
            status = solution_result.get('result', {}).get('status', 'unknown')
            obj_value = solution_result.get('result', {}).get('objective_value', 0)
            print(f"✅ Solution Status: {status}")
            print(f"   Objective Value: {obj_value}")
            print(f"   Solve Time: {solution_result.get('result', {}).get('solve_time', 0):.2f}s")
            
            # Step 5: Business Impact Analysis
            business_impact = solution_result.get('result', {}).get('business_impact', {})
            if business_impact:
                print(f"\n💰 Business Impact:")
                print(f"   Profit: ${business_impact.get('total_profit', 0):,.2f}")
                print(f"   Cost Savings: ${business_impact.get('cost_savings', 0):,.2f}")
                print(f"   Capacity Utilization: {business_impact.get('capacity_utilization', '0%')}")
            
            results["status"] = "success"
            results["message"] = "Complete workflow executed successfully"
            
        except Exception as e:
            print(f"❌ Error in workflow: {str(e)}")
            results["status"] = "error"
            results["error"] = str(e)
            results["message"] = "Workflow execution failed"
        
        return results
    
    async def test_workflow_templates(self) -> dict:
        """Test the workflow templates functionality."""
        print(f"\n{'='*60}")
        print(f"📋 TESTING: Workflow Templates")
        print(f"{'='*60}")
        
        try:
            templates_result = await get_workflow_templates()
            print(f"✅ Retrieved {templates_result.get('total_workflows', 0)} workflow templates")
            print(f"   Industries: {templates_result.get('industries', 0)}")
            
            return {
                "status": "success",
                "result": templates_result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Error retrieving templates: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_workflow_execution(self) -> dict:
        """Test workflow execution with a sample workflow."""
        print(f"\n{'='*60}")
        print(f"🚀 TESTING: Workflow Execution")
        print(f"{'='*60}")
        
        try:
            # Test manufacturing workflow execution
            workflow_result = await execute_workflow(
                industry="manufacturing",
                workflow_id="production_planning",
                parameters={
                    "production_lines": 3,
                    "products": 15,
                    "time_horizon": "quarterly",
                    "constraints": ["labor", "material", "capacity"]
                }
            )
            
            print(f"✅ Workflow executed successfully")
            print(f"   Industry: {workflow_result.get('industry', 'unknown')}")
            print(f"   Workflow ID: {workflow_result.get('workflow_id', 'unknown')}")
            print(f"   Execution Time: {workflow_result.get('execution_time', 0):.2f}s")
            
            return {
                "status": "success",
                "result": workflow_result,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ Error executing workflow: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_all_tests(self) -> dict:
        """Run all tests and generate a comprehensive report."""
        print(f"🚀 Starting DcisionAI MCP Server Tests")
        print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🔧 Testing {len(self.test_queries)} customer queries")
        
        test_results = {
            "test_session": {
                "timestamp": datetime.now().isoformat(),
                "total_queries": len(self.test_queries),
                "tests_run": []
            }
        }
        
        # Test individual customer queries
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n{'='*80}")
            print(f"TEST {i}/{len(self.test_queries)}")
            result = await self.test_single_query(query)
            test_results["test_session"]["tests_run"].append(result)
        
        # Test workflow templates
        templates_result = await self.test_workflow_templates()
        test_results["workflow_templates"] = templates_result
        
        # Test workflow execution
        execution_result = await self.test_workflow_execution()
        test_results["workflow_execution"] = execution_result
        
        # Generate summary
        successful_tests = sum(1 for test in test_results["test_session"]["tests_run"] if test.get("status") == "success")
        total_tests = len(test_results["test_session"]["tests_run"])
        
        print(f"\n{'='*80}")
        print(f"📊 TEST SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Successful Tests: {successful_tests}/{total_tests}")
        print(f"📋 Workflow Templates: {'✅' if templates_result.get('status') == 'success' else '❌'}")
        print(f"🚀 Workflow Execution: {'✅' if execution_result.get('status') == 'success' else '❌'}")
        
        # Save results to file
        results_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        print(f"\n💾 Results saved to: {results_file}")
        
        return test_results

async def main():
    """Main test execution function."""
    try:
        tester = CustomerQueryTester()
        results = await tester.run_all_tests()
        
        # Check if all tests passed
        all_passed = all(
            test.get("status") == "success" 
            for test in results["test_session"]["tests_run"]
        ) and results["workflow_templates"].get("status") == "success"
        
        if all_passed:
            print(f"\n🎉 ALL TESTS PASSED! MCP Server is working correctly.")
            return 0
        else:
            print(f"\n⚠️  SOME TESTS FAILED. Check the results for details.")
            return 1
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
