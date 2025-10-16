#!/usr/bin/env python3
"""
Skeptical Analysis of MCP Server Test Results
============================================

This script performs a critical, scientific analysis of the test results to identify:
1. Potential AI hallucinations or unrealistic responses
2. Mathematical inconsistencies
3. Business metric validity
4. Response time anomalies
5. Data quality issues
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any, Tuple

class SkepticalAnalyzer:
    """Critical analyzer for MCP server test results."""
    
    def __init__(self, results_file: str):
        self.results_file = results_file
        self.results = self._load_results()
        self.issues = []
        self.warnings = []
        self.anomalies = []
    
    def _load_results(self) -> Dict[str, Any]:
        """Load test results from JSON file."""
        with open(self.results_file, 'r') as f:
            return json.load(f)
    
    def analyze_all(self) -> Dict[str, Any]:
        """Perform comprehensive skeptical analysis."""
        print("🔍 SKEPTICAL ANALYSIS OF MCP SERVER TEST RESULTS")
        print("=" * 60)
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": 0,
            "critical_issues": [],
            "warnings": [],
            "anomalies": [],
            "verification_results": {}
        }
        
        # 1. Analyze AI Response Patterns
        print("\n1. 🤖 AI RESPONSE PATTERN ANALYSIS")
        ai_analysis = self._analyze_ai_responses()
        analysis["verification_results"]["ai_responses"] = ai_analysis
        
        # 2. Mathematical Validity Check
        print("\n2. 🧮 MATHEMATICAL VALIDITY CHECK")
        math_analysis = self._analyze_mathematical_validity()
        analysis["verification_results"]["mathematical_validity"] = math_analysis
        
        # 3. Business Metrics Verification
        print("\n3. 💼 BUSINESS METRICS VERIFICATION")
        business_analysis = self._analyze_business_metrics()
        analysis["verification_results"]["business_metrics"] = business_analysis
        
        # 4. Response Time Analysis
        print("\n4. ⏱️ RESPONSE TIME ANALYSIS")
        timing_analysis = self._analyze_response_times()
        analysis["verification_results"]["response_times"] = timing_analysis
        
        # 5. Data Consistency Check
        print("\n5. 🔄 DATA CONSISTENCY CHECK")
        consistency_analysis = self._analyze_data_consistency()
        analysis["verification_results"]["data_consistency"] = consistency_analysis
        
        # 6. Error Pattern Analysis
        print("\n6. ❌ ERROR PATTERN ANALYSIS")
        error_analysis = self._analyze_error_patterns()
        analysis["verification_results"]["error_patterns"] = error_analysis
        
        # Compile final results
        analysis["critical_issues"] = self.issues
        analysis["warnings"] = self.warnings
        analysis["anomalies"] = self.anomalies
        analysis["total_issues"] = len(self.issues) + len(self.warnings) + len(self.anomalies)
        
        return analysis
    
    def _analyze_ai_responses(self) -> Dict[str, Any]:
        """Analyze AI responses for potential hallucinations."""
        print("   Checking for AI hallucinations and unrealistic responses...")
        
        issues = []
        warnings = []
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            
            # Check objective values for unrealistic patterns
            obj_value = test["steps"]["optimization_solution"]["result"]["objective_value"]
            if obj_value > 1000000:  # Suspiciously high values
                issues.append(f"CRITICAL: {test_name} has unrealistic objective value: {obj_value}")
            
            # Check for identical or very similar objective values across different problems
            if abs(obj_value - 1254782.3) < 1000:  # Very similar to first test
                warnings.append(f"WARNING: {test_name} has suspiciously similar objective value: {obj_value}")
            
            # Check business impact metrics
            business_impact = test["steps"]["optimization_solution"]["result"]["business_impact"]
            
            # Check for unrealistic profit increases
            if "profit_increase" in business_impact:
                profit_inc = business_impact["profit_increase"]
                if isinstance(profit_inc, (int, float)) and profit_inc > 50:
                    warnings.append(f"WARNING: {test_name} shows unrealistic profit increase: {profit_inc}%")
            
            # Check for zero cost savings in healthcare (suspicious)
            if test_name == "Healthcare Resource Allocation":
                if business_impact.get("cost_savings", 0) == 0:
                    warnings.append(f"WARNING: Healthcare optimization shows zero cost savings - suspicious")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "total_checks": len(self.results["test_session"]["tests_run"]) * 4
        }
    
    def _analyze_mathematical_validity(self) -> Dict[str, Any]:
        """Check mathematical formulations for validity."""
        print("   Validating mathematical formulations...")
        
        issues = []
        warnings = []
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            model_result = test["steps"]["model_building"]["result"]
            
            # Check if variables match between model building and solution
            model_vars = model_result.get("variables", [])
            solution_vars = test["steps"]["optimization_solution"]["result"].get("optimal_values", {})
            
            # Count variables
            model_var_count = len(model_vars)
            solution_var_count = len(solution_vars)
            
            if model_var_count != solution_var_count:
                issues.append(f"CRITICAL: {test_name} - Variable count mismatch: model={model_var_count}, solution={solution_var_count}")
            
            # Check for unrealistic variable bounds
            for var in model_vars:
                bounds = var.get("bounds", "")
                if "1000" in str(bounds) and "10000" in str(bounds):
                    warnings.append(f"WARNING: {test_name} - Variable {var['name']} has suspiciously round bounds: {bounds}")
            
            # Check constraint count vs variable count ratio
            constraints = model_result.get("constraints", [])
            if len(constraints) < len(model_vars) * 0.5:
                warnings.append(f"WARNING: {test_name} - Low constraint-to-variable ratio: {len(constraints)}/{len(model_vars)}")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "total_checks": len(self.results["test_session"]["tests_run"]) * 3
        }
    
    def _analyze_business_metrics(self) -> Dict[str, Any]:
        """Verify business metrics for realism."""
        print("   Verifying business impact metrics...")
        
        issues = []
        warnings = []
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            business_impact = test["steps"]["optimization_solution"]["result"]["business_impact"]
            
            # Check utilization percentages
            for metric in ["labor_utilization", "material_utilization", "machine_utilization", "capacity_utilization"]:
                if metric in business_impact:
                    util = business_impact[metric]
                    if isinstance(util, (int, float)):
                        if util > 100:
                            issues.append(f"CRITICAL: {test_name} - {metric} exceeds 100%: {util}%")
                        elif util > 95:
                            warnings.append(f"WARNING: {test_name} - {metric} is suspiciously high: {util}%")
            
            # Check for missing units in cost savings
            if "cost_savings" in business_impact:
                savings = business_impact["cost_savings"]
                if isinstance(savings, (int, float)) and savings < 1000:
                    warnings.append(f"WARNING: {test_name} - Cost savings seem low: {savings} (units unclear)")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "total_checks": len(self.results["test_session"]["tests_run"]) * 5
        }
    
    def _analyze_response_times(self) -> Dict[str, Any]:
        """Analyze response times for anomalies."""
        print("   Analyzing response time patterns...")
        
        issues = []
        warnings = []
        times = []
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            
            # Extract solve times
            solve_time = test["steps"]["optimization_solution"]["result"].get("solve_time", 0)
            times.append(solve_time)
            
            # Check for unrealistic solve times
            if solve_time < 0.1:
                warnings.append(f"WARNING: {test_name} - Suspiciously fast solve time: {solve_time}s")
            elif solve_time > 100:
                warnings.append(f"WARNING: {test_name} - Suspiciously slow solve time: {solve_time}s")
            
            # Check for identical solve times (suspicious)
            if solve_time == 14.7:  # First test's solve time
                warnings.append(f"WARNING: {test_name} - Identical solve time to first test: {solve_time}s")
        
        # Check for patterns in solve times
        if len(set(times)) < len(times) * 0.5:
            issues.append("CRITICAL: Too many identical solve times - suggests AI generation rather than real solving")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "solve_times": times,
            "average_solve_time": sum(times) / len(times) if times else 0
        }
    
    def _analyze_data_consistency(self) -> Dict[str, Any]:
        """Check data consistency across steps."""
        print("   Checking data consistency across workflow steps...")
        
        issues = []
        warnings = []
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            
            # Check if entities identified in data analysis match model variables
            data_entities = test["steps"]["data_analysis"]["result"].get("entities", 0)
            model_vars = len(test["steps"]["model_building"]["result"].get("variables", []))
            
            if abs(data_entities - model_vars) > 5:
                warnings.append(f"WARNING: {test_name} - Large gap between data entities ({data_entities}) and model variables ({model_vars})")
            
            # Check if complexity assessment is consistent
            intent_complexity = test["steps"]["intent_classification"]["result"].get("complexity", "")
            model_complexity = test["steps"]["model_building"]["result"].get("model_complexity", "")
            
            if intent_complexity != model_complexity:
                warnings.append(f"WARNING: {test_name} - Complexity mismatch: intent={intent_complexity}, model={model_complexity}")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "total_checks": len(self.results["test_session"]["tests_run"]) * 2
        }
    
    def _analyze_error_patterns(self) -> Dict[str, Any]:
        """Analyze error patterns and fallback usage."""
        print("   Analyzing error patterns and fallback mechanisms...")
        
        issues = []
        warnings = []
        
        # Check for Bearer token errors
        if "workflow_execution" in self.results:
            workflow_result = self.results["workflow_execution"]["result"]
            if workflow_result.get("status") == "error":
                error_msg = workflow_result.get("error", "")
                if "Bearer" in error_msg:
                    issues.append("CRITICAL: Authentication errors in workflow execution - Bearer token issues")
        
        # Check for fallback usage
        fallback_count = 0
        for test in self.results["test_session"]["tests_run"]:
            if "fallback" in str(test):
                fallback_count += 1
        
        if fallback_count > 0:
            warnings.append(f"WARNING: {fallback_count} tests used fallback mechanisms - may indicate system issues")
        
        return {
            "issues": issues,
            "warnings": warnings,
            "fallback_usage": fallback_count
        }
    
    def generate_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a comprehensive skeptical analysis report."""
        report = []
        report.append("🔍 SKEPTICAL ANALYSIS REPORT")
        report.append("=" * 50)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Issues Found: {analysis['total_issues']}")
        report.append("")
        
        if analysis["critical_issues"]:
            report.append("🚨 CRITICAL ISSUES:")
            for issue in analysis["critical_issues"]:
                report.append(f"  ❌ {issue}")
            report.append("")
        
        if analysis["warnings"]:
            report.append("⚠️ WARNINGS:")
            for warning in analysis["warnings"]:
                report.append(f"  ⚠️ {warning}")
            report.append("")
        
        if analysis["anomalies"]:
            report.append("🔍 ANOMALIES:")
            for anomaly in analysis["anomalies"]:
                report.append(f"  🔍 {anomaly}")
            report.append("")
        
        # Summary assessment
        if analysis["total_issues"] == 0:
            report.append("✅ ASSESSMENT: Results appear legitimate with no major issues detected.")
        elif len(analysis["critical_issues"]) == 0:
            report.append("⚠️ ASSESSMENT: Results show some concerns but no critical issues.")
        else:
            report.append("❌ ASSESSMENT: Results contain critical issues that require investigation.")
        
        return "\n".join(report)

def main():
    """Run skeptical analysis on test results."""
    results_file = "test_results_20251016_022025.json"
    
    try:
        analyzer = SkepticalAnalyzer(results_file)
        analysis = analyzer.analyze_all()
        
        # Generate and print report
        report = analyzer.generate_report(analysis)
        print("\n" + "="*60)
        print(report)
        
        # Save detailed analysis
        analysis_file = f"skeptical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        print(f"\n💾 Detailed analysis saved to: {analysis_file}")
        
        return 0 if len(analysis["critical_issues"]) == 0 else 1
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
