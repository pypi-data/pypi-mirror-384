#!/usr/bin/env python3
"""
Portfolio Optimization Results Analysis
======================================

Analyze the portfolio optimization results with skeptical scrutiny.
"""

import json
from datetime import datetime

def analyze_portfolio_results(results_file: str):
    """Analyze portfolio optimization results."""
    
    with open(results_file, 'r') as f:
        results = json.load(f)
    
    print("🔬 PORTFOLIO OPTIMIZATION SKEPTICAL ANALYSIS")
    print("=" * 60)
    print(f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Test: {results.get('test_name', 'Unknown')}")
    
    # Extract key results
    intent_result = results.get('intent_classification', {}).get('result', {})
    data_result = results.get('data_analysis', {}).get('result', {})
    model_result = results.get('model_building', {}).get('result', {})
    solution_result = results.get('optimization_solution', {}).get('result', {})
    
    print(f"\n📊 RESULTS SUMMARY:")
    print(f"   Intent: {intent_result.get('intent', 'unknown')}")
    print(f"   Industry: {intent_result.get('industry', 'unknown')}")
    print(f"   Complexity: {intent_result.get('complexity', 'unknown')}")
    print(f"   Data Readiness: {data_result.get('readiness_score', 0):.2f}")
    print(f"   Model Type: {model_result.get('model_type', 'unknown')}")
    print(f"   Variables: {len(model_result.get('variables', []))}")
    print(f"   Constraints: {len(model_result.get('constraints', []))}")
    print(f"   Solution Status: {solution_result.get('status', 'unknown')}")
    print(f"   Objective Value: {solution_result.get('objective_value', 0)}")
    print(f"   Solve Time: {solution_result.get('solve_time', 0):.3f}s")
    
    # Skeptical analysis
    print(f"\n🔍 SKEPTICAL ANALYSIS:")
    
    concerns = []
    warnings = []
    
    # 1. Check objective value
    obj_value = solution_result.get('objective_value', 0)
    if obj_value > 1000000:
        concerns.append("❌ CRITICAL: Unrealistically high objective value")
    elif obj_value > 100000:
        warnings.append("⚠️ WARNING: High objective value")
    else:
        print("✅ Objective value appears realistic")
    
    # 2. Check solve time
    solve_time = solution_result.get('solve_time', 0)
    if solve_time < 0.001:
        warnings.append("⚠️ WARNING: Suspiciously fast solve time")
    elif solve_time > 10:
        warnings.append("⚠️ WARNING: Suspiciously slow solve time")
    else:
        print("✅ Solve time appears realistic")
    
    # 3. Check model complexity
    variables = model_result.get('variables', [])
    constraints = model_result.get('constraints', [])
    
    if len(variables) >= 10:
        print("✅ High variable count indicates complex model")
    else:
        warnings.append("⚠️ WARNING: Low variable count for portfolio optimization")
    
    if len(constraints) >= 5:
        print("✅ Adequate constraint count")
    else:
        warnings.append("⚠️ WARNING: Low constraint count for portfolio optimization")
    
    # 4. Check optimal values
    optimal_values = solution_result.get('optimal_values', {})
    if optimal_values:
        total_allocation = sum(v for v in optimal_values.values() if isinstance(v, (int, float)))
        if 0.9 <= total_allocation <= 1.1:
            print("✅ Total allocation is realistic (~100%)")
        else:
            concerns.append(f"❌ CRITICAL: Unrealistic total allocation: {total_allocation}")
        
        # Check for diversification
        non_zero_values = [v for v in optimal_values.values() if isinstance(v, (int, float)) and v > 0.01]
        if len(non_zero_values) >= 2:
            print("✅ Portfolio shows diversification")
        else:
            warnings.append("⚠️ WARNING: Low portfolio diversification")
    
    # 5. Check business impact
    business_impact = solution_result.get('business_impact', {})
    if business_impact:
        profit_increase = business_impact.get('profit_increase', '0%')
        if isinstance(profit_increase, str) and profit_increase.endswith('%'):
            try:
                profit_pct = float(profit_increase.replace('%', ''))
                if profit_pct > 50:
                    concerns.append("❌ CRITICAL: Unrealistic profit increase")
                elif profit_pct > 25:
                    warnings.append("⚠️ WARNING: High profit increase")
                else:
                    print("✅ Profit increase appears realistic")
            except:
                warnings.append("⚠️ WARNING: Could not parse profit increase")
    
    # Display concerns and warnings
    if concerns:
        print(f"\n🚨 CRITICAL CONCERNS:")
        for concern in concerns:
            print(f"   {concern}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS:")
        for warning in warnings:
            print(f"   {warning}")
    
    # Overall verdict
    print(f"\n🎯 OVERALL VERDICT:")
    if concerns:
        print("❌ Results contain CRITICAL issues that suggest problems with the optimization.")
    elif len(warnings) > 3:
        print("⚠️ Results show multiple concerns that warrant investigation.")
    elif warnings:
        print("🔍 Results show some minor concerns but appear generally legitimate.")
    else:
        print("✅ Results appear legitimate with no major concerns detected.")
    
    # Complexity assessment
    print(f"\n📈 COMPLEXITY ASSESSMENT:")
    complexity_score = 0
    
    if len(variables) >= 10:
        complexity_score += 2
    elif len(variables) >= 5:
        complexity_score += 1
    
    if len(constraints) >= 8:
        complexity_score += 2
    elif len(constraints) >= 5:
        complexity_score += 1
    
    if model_result.get('model_type', '').lower() in ['mixed_integer_linear_programming', 'milp']:
        complexity_score += 2
    elif 'linear' in model_result.get('model_type', '').lower():
        complexity_score += 1
    
    if solve_time > 0.01:
        complexity_score += 1
    
    print(f"   Complexity Score: {complexity_score}/6")
    if complexity_score >= 5:
        print("   ✅ High complexity - sophisticated optimization")
    elif complexity_score >= 3:
        print("   🔍 Medium complexity - moderate optimization")
    else:
        print("   ⚠️ Low complexity - simple optimization")
    
    return {
        "concerns": concerns,
        "warnings": warnings,
        "complexity_score": complexity_score,
        "total_issues": len(concerns) + len(warnings)
    }

if __name__ == "__main__":
    results_file = "simple_portfolio_results_20251016_023631.json"
    analysis = analyze_portfolio_results(results_file)
    
    print(f"\n📊 FINAL ASSESSMENT:")
    print(f"   Total Issues: {analysis['total_issues']}")
    print(f"   Complexity Score: {analysis['complexity_score']}/6")
    
    if analysis['total_issues'] == 0:
        print("🎉 EXCELLENT: No issues detected - results appear legitimate!")
    elif analysis['total_issues'] <= 2:
        print("✅ GOOD: Minor issues only - results appear mostly legitimate")
    else:
        print("⚠️ CONCERN: Multiple issues detected - results need investigation")
