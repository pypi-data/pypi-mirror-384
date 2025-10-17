#!/usr/bin/env python3
"""
Deep Skeptical Analysis - Manual Critical Review
===============================================

This script performs a more rigorous, manual analysis focusing on:
1. AI response patterns that suggest generation rather than real computation
2. Mathematical inconsistencies and unrealistic values
3. Business logic flaws
4. Response time anomalies
5. Data flow inconsistencies
"""

import json
import re
from datetime import datetime
from typing import Dict, List, Any

class DeepSkepticalAnalyzer:
    """Deep critical analyzer with manual pattern detection."""
    
    def __init__(self, results_file: str):
        self.results_file = results_file
        self.results = self._load_results()
        self.critical_findings = []
        self.suspicious_patterns = []
        self.mathematical_issues = []
    
    def _load_results(self) -> Dict[str, Any]:
        """Load test results from JSON file."""
        with open(self.results_file, 'r') as f:
            return json.load(f)
    
    def deep_analysis(self) -> Dict[str, Any]:
        """Perform deep skeptical analysis."""
        print("🔬 DEEP SKEPTICAL ANALYSIS - MANUAL CRITICAL REVIEW")
        print("=" * 60)
        
        # 1. Analyze Objective Value Patterns
        self._analyze_objective_value_patterns()
        
        # 2. Check Mathematical Formulation Quality
        self._analyze_mathematical_formulations()
        
        # 3. Verify Business Impact Realism
        self._analyze_business_impact_realism()
        
        # 4. Examine Response Time Patterns
        self._analyze_response_time_patterns()
        
        # 5. Check Data Flow Consistency
        self._analyze_data_flow_consistency()
        
        # 6. Detect AI Generation Patterns
        self._detect_ai_generation_patterns()
        
        return {
            "critical_findings": self.critical_findings,
            "suspicious_patterns": self.suspicious_patterns,
            "mathematical_issues": self.mathematical_issues,
            "total_concerns": len(self.critical_findings) + len(self.suspicious_patterns) + len(self.mathematical_issues)
        }
    
    def _analyze_objective_value_patterns(self):
        """Analyze objective values for suspicious patterns."""
        print("\n1. 🎯 OBJECTIVE VALUE PATTERN ANALYSIS")
        
        obj_values = []
        for test in self.results["test_session"]["tests_run"]:
            obj_value = test["steps"]["optimization_solution"]["result"]["objective_value"]
            obj_values.append(obj_value)
            print(f"   {test['query_name']}: {obj_value}")
        
        # Check for suspiciously similar values
        if len(set(obj_values)) < len(obj_values):
            self.critical_findings.append("CRITICAL: Identical objective values across different optimization problems - this is mathematically impossible")
        
        # Check for unrealistic precision
        for i, value in enumerate(obj_values):
            if value > 1000000:
                self.suspicious_patterns.append(f"Suspicious: Test {i+1} has extremely high objective value ({value}) - suggests AI generation")
            
            # Check for suspiciously round numbers
            if value % 1000 == 0 and value > 10000:
                self.suspicious_patterns.append(f"Suspicious: Test {i+1} has suspiciously round objective value ({value})")
    
    def _analyze_mathematical_formulations(self):
        """Analyze mathematical formulations for quality and realism."""
        print("\n2. 🧮 MATHEMATICAL FORMULATION ANALYSIS")
        
        for i, test in enumerate(self.results["test_session"]["tests_run"]):
            test_name = test["query_name"]
            model_result = test["steps"]["model_building"]["result"]
            
            print(f"   Analyzing {test_name}...")
            
            # Check variable definitions
            variables = model_result.get("variables", [])
            print(f"     Variables: {len(variables)}")
            
            # Check for unrealistic variable bounds
            for var in variables:
                bounds = str(var.get("bounds", ""))
                if "1000" in bounds or "10000" in bounds:
                    self.suspicious_patterns.append(f"Suspicious: {test_name} has suspiciously round variable bounds: {bounds}")
            
            # Check constraint quality
            constraints = model_result.get("constraints", [])
            print(f"     Constraints: {len(constraints)}")
            
            # Check for generic constraint descriptions
            generic_descriptions = ["capacity", "demand", "labor", "material", "quality"]
            generic_count = sum(1 for c in constraints if any(g in c.get("description", "").lower() for g in generic_descriptions))
            
            if generic_count > len(constraints) * 0.7:
                self.suspicious_patterns.append(f"Suspicious: {test_name} has too many generic constraint descriptions - suggests AI template usage")
            
            # Check mathematical formulation complexity
            formulation = model_result.get("mathematical_formulation", "")
            if len(formulation) < 200:
                self.mathematical_issues.append(f"Mathematical Issue: {test_name} has suspiciously short mathematical formulation")
    
    def _analyze_business_impact_realism(self):
        """Analyze business impact metrics for realism."""
        print("\n3. 💼 BUSINESS IMPACT REALISM ANALYSIS")
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            business_impact = test["steps"]["optimization_solution"]["result"]["business_impact"]
            
            print(f"   Analyzing {test_name} business impact...")
            
            # Check for unrealistic profit increases
            profit_increase = business_impact.get("profit_increase", 0)
            if isinstance(profit_increase, (int, float)):
                if profit_increase > 30:
                    self.critical_findings.append(f"CRITICAL: {test_name} shows unrealistic profit increase: {profit_increase}%")
                elif profit_increase > 20:
                    self.suspicious_patterns.append(f"Suspicious: {test_name} shows high profit increase: {profit_increase}%")
            
            # Check utilization metrics
            for metric in ["labor_utilization", "material_utilization", "machine_utilization"]:
                if metric in business_impact:
                    util = business_impact[metric]
                    if isinstance(util, (int, float)):
                        if util > 95:
                            self.suspicious_patterns.append(f"Suspicious: {test_name} has suspiciously high {metric}: {util}%")
            
            # Check cost savings
            cost_savings = business_impact.get("cost_savings", 0)
            if isinstance(cost_savings, (int, float)) and cost_savings < 100:
                self.suspicious_patterns.append(f"Suspicious: {test_name} has suspiciously low cost savings: {cost_savings}")
    
    def _analyze_response_time_patterns(self):
        """Analyze response times for suspicious patterns."""
        print("\n4. ⏱️ RESPONSE TIME PATTERN ANALYSIS")
        
        solve_times = []
        for test in self.results["test_session"]["tests_run"]:
            solve_time = test["steps"]["optimization_solution"]["result"].get("solve_time", 0)
            solve_times.append(solve_time)
            print(f"   {test['query_name']}: {solve_time}s")
        
        # Check for suspiciously similar solve times
        if len(set(solve_times)) < len(solve_times) * 0.7:
            self.critical_findings.append("CRITICAL: Too many similar solve times - suggests AI generation rather than real optimization")
        
        # Check for unrealistic solve times
        for i, time in enumerate(solve_times):
            if time < 0.5:
                self.suspicious_patterns.append(f"Suspicious: Test {i+1} has unrealistically fast solve time: {time}s")
            elif time > 60:
                self.suspicious_patterns.append(f"Suspicious: Test {i+1} has suspiciously slow solve time: {time}s")
    
    def _analyze_data_flow_consistency(self):
        """Analyze data flow consistency across workflow steps."""
        print("\n5. 🔄 DATA FLOW CONSISTENCY ANALYSIS")
        
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            
            # Check entity count consistency
            data_entities = test["steps"]["data_analysis"]["result"].get("entities", 0)
            model_vars = len(test["steps"]["model_building"]["result"].get("variables", []))
            solution_vars = len(test["steps"]["optimization_solution"]["result"].get("optimal_values", {}))
            
            print(f"   {test_name}:")
            print(f"     Data entities: {data_entities}")
            print(f"     Model variables: {model_vars}")
            print(f"     Solution variables: {solution_vars}")
            
            # Check for major inconsistencies
            if abs(data_entities - model_vars) > 10:
                self.suspicious_patterns.append(f"Suspicious: {test_name} has large gap between data entities ({data_entities}) and model variables ({model_vars})")
            
            if model_vars != solution_vars:
                self.critical_findings.append(f"CRITICAL: {test_name} has variable count mismatch between model ({model_vars}) and solution ({solution_vars})")
    
    def _detect_ai_generation_patterns(self):
        """Detect patterns that suggest AI generation rather than real computation."""
        print("\n6. 🤖 AI GENERATION PATTERN DETECTION")
        
        # Check for template-like responses
        template_phrases = [
            "High quality, proven optimal",
            "Solution is robust up to",
            "Solution can accommodate",
            "Focus production on high-profit products",
            "Invest in additional",
            "Explore opportunities to"
        ]
        
        template_count = 0
        for test in self.results["test_session"]["tests_run"]:
            test_name = test["query_name"]
            
            # Check recommendations for template phrases
            recommendations = test["steps"]["optimization_solution"]["result"].get("recommendations", [])
            for rec in recommendations:
                for phrase in template_phrases:
                    if phrase in rec:
                        template_count += 1
                        break
            
            # Check solution quality descriptions
            solution_quality = test["steps"]["optimization_solution"]["result"].get("solution_quality", "")
            if "High quality" in solution_quality:
                template_count += 1
        
        if template_count > 5:
            self.critical_findings.append(f"CRITICAL: High template phrase usage ({template_count}) suggests AI generation rather than real analysis")
        elif template_count > 2:
            self.suspicious_patterns.append(f"Suspicious: Template phrase usage ({template_count}) suggests some AI generation")
    
    def generate_critical_report(self, analysis: Dict[str, Any]) -> str:
        """Generate a critical assessment report."""
        report = []
        report.append("🔬 DEEP SKEPTICAL ANALYSIS REPORT")
        report.append("=" * 50)
        report.append(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Total Concerns: {analysis['total_concerns']}")
        report.append("")
        
        if self.critical_findings:
            report.append("🚨 CRITICAL FINDINGS:")
            for finding in self.critical_findings:
                report.append(f"  ❌ {finding}")
            report.append("")
        
        if self.suspicious_patterns:
            report.append("⚠️ SUSPICIOUS PATTERNS:")
            for pattern in self.suspicious_patterns:
                report.append(f"  ⚠️ {pattern}")
            report.append("")
        
        if self.mathematical_issues:
            report.append("🧮 MATHEMATICAL ISSUES:")
            for issue in self.mathematical_issues:
                report.append(f"  🔍 {issue}")
            report.append("")
        
        # Overall assessment
        if len(self.critical_findings) > 0:
            report.append("❌ VERDICT: Results contain CRITICAL issues that strongly suggest AI generation rather than real optimization.")
            report.append("   The MCP server appears to be generating plausible-looking but artificial results.")
        elif len(self.suspicious_patterns) > 3:
            report.append("⚠️ VERDICT: Results show multiple suspicious patterns that warrant investigation.")
            report.append("   While not definitively fake, the results raise significant concerns.")
        elif len(self.suspicious_patterns) > 0:
            report.append("🔍 VERDICT: Results show some suspicious patterns but may still be legitimate.")
            report.append("   Further investigation recommended.")
        else:
            report.append("✅ VERDICT: Results appear legitimate with no major concerns detected.")
        
        return "\n".join(report)

def main():
    """Run deep skeptical analysis."""
    results_file = "simple_portfolio_results_20251016_023631.json"
    
    try:
        analyzer = DeepSkepticalAnalyzer(results_file)
        analysis = analyzer.deep_analysis()
        
        # Generate and print report
        report = analyzer.generate_critical_report(analysis)
        print("\n" + "="*60)
        print(report)
        
        # Save detailed analysis
        analysis_file = f"deep_skeptical_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(analysis_file, 'w') as f:
            json.dump({
                "analysis": analysis,
                "critical_findings": analyzer.critical_findings,
                "suspicious_patterns": analyzer.suspicious_patterns,
                "mathematical_issues": analyzer.mathematical_issues
            }, f, indent=2)
        
        print(f"\n💾 Detailed analysis saved to: {analysis_file}")
        
        return 1 if len(analyzer.critical_findings) > 0 else 0
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
