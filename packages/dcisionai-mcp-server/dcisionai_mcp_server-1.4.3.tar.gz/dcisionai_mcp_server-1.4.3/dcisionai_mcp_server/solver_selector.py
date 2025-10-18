#!/usr/bin/env python3
"""
Solver Selection Module for DcisionAI MCP Server
===============================================

This module provides intelligent solver selection based on optimization problem type,
available solvers, and problem characteristics.
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SolverInfo:
    """Information about a solver."""
    name: str
    optimization_types: List[str]
    capabilities: List[str]
    performance_rating: int  # 1-10
    is_available: bool = False

class SolverSelector:
    """
    Intelligent solver selection for optimization problems.
    
    Selects the best available solver based on:
    - Optimization problem type (LP, QP, MILP, etc.)
    - Problem size and characteristics
    - Available solvers on the system
    - Performance requirements
    """
    
    def __init__(self):
        """Initialize the solver selector."""
        self.available_solvers = self._detect_available_solvers()
        self.solver_database = self._build_solver_database()
        
    def _build_solver_database(self) -> Dict[str, SolverInfo]:
        """Build database of available solvers with their capabilities."""
        return {
            # OR-Tools Linear Programming Solvers
            "GLOP": SolverInfo(
                name="GLOP",
                optimization_types=["linear_programming"],
                capabilities=["linear_constraints", "continuous_variables"],
                performance_rating=8,
                is_available="GLOP" in self.available_solvers
            ),
            "PDLP": SolverInfo(
                name="PDLP",
                optimization_types=["linear_programming"],
                capabilities=["linear_constraints", "continuous_variables", "large_scale"],
                performance_rating=9,
                is_available="PDLP" in self.available_solvers
            ),
            "CBC": SolverInfo(
                name="CBC",
                optimization_types=["linear_programming", "mixed_integer_linear_programming"],
                capabilities=["linear_constraints", "continuous_variables", "integer_variables", "binary_variables"],
                performance_rating=7,
                is_available="CBC" in self.available_solvers
            ),
            "SCIP": SolverInfo(
                name="SCIP",
                optimization_types=["linear_programming", "mixed_integer_linear_programming", "mixed_integer_quadratic_programming"],
                capabilities=["linear_constraints", "quadratic_constraints", "continuous_variables", "integer_variables", "binary_variables"],
                performance_rating=9,
                is_available="SCIP" in self.available_solvers
            ),
            
            # COIN-OR Solvers
            "GLPK": SolverInfo(
                name="GLPK",
                optimization_types=["linear_programming", "mixed_integer_linear_programming"],
                capabilities=["linear_constraints", "continuous_variables", "integer_variables", "binary_variables"],
                performance_rating=6,
                is_available="GLPK" in self.available_solvers
            ),
            "CLP": SolverInfo(
                name="CLP",
                optimization_types=["linear_programming"],
                capabilities=["linear_constraints", "continuous_variables"],
                performance_rating=7,
                is_available="CLP" in self.available_solvers
            ),
            "SYMPHONY": SolverInfo(
                name="SYMPHONY",
                optimization_types=["mixed_integer_linear_programming"],
                capabilities=["linear_constraints", "continuous_variables", "integer_variables", "binary_variables", "parallel"],
                performance_rating=8,
                is_available="SYMPHONY" in self.available_solvers
            ),
            
            # HiGHS Solver
            "HIGHS": SolverInfo(
                name="HIGHS",
                optimization_types=["linear_programming", "mixed_integer_linear_programming"],
                capabilities=["linear_constraints", "continuous_variables", "integer_variables", "binary_variables", "large_scale"],
                performance_rating=9,
                is_available="HIGHS" in self.available_solvers
            ),
            
            # Quadratic Programming Solvers
            "OSQP": SolverInfo(
                name="OSQP",
                optimization_types=["quadratic_programming"],
                capabilities=["quadratic_constraints", "continuous_variables", "convex_optimization"],
                performance_rating=8,
                is_available="OSQP" in self.available_solvers
            ),
            "ECOS": SolverInfo(
                name="ECOS",
                optimization_types=["quadratic_programming", "second_order_cone_programming"],
                capabilities=["quadratic_constraints", "continuous_variables", "convex_optimization"],
                performance_rating=7,
                is_available="ECOS" in self.available_solvers
            ),
            "CVXOPT": SolverInfo(
                name="CVXOPT",
                optimization_types=["quadratic_programming", "second_order_cone_programming", "semidefinite_programming"],
                capabilities=["quadratic_constraints", "continuous_variables", "convex_optimization", "socp", "sdp"],
                performance_rating=7,
                is_available="CVXOPT" in self.available_solvers
            ),
            "SCS": SolverInfo(
                name="SCS",
                optimization_types=["quadratic_programming", "second_order_cone_programming", "semidefinite_programming"],
                capabilities=["quadratic_constraints", "continuous_variables", "convex_optimization", "socp", "sdp"],
                performance_rating=8,
                is_available="SCS" in self.available_solvers
            ),
            
            # CVXPY Ecosystem
            "CVXPY": SolverInfo(
                name="CVXPY",
                optimization_types=["linear_programming", "quadratic_programming", "second_order_cone_programming", "semidefinite_programming"],
                capabilities=["linear_constraints", "quadratic_constraints", "continuous_variables", "convex_optimization", "socp", "sdp", "disciplined_convex_programming"],
                performance_rating=9,
                is_available="CVXPY" in self.available_solvers
            ),
            
            # Specialized Solvers
            "MOSEK": SolverInfo(
                name="MOSEK",
                optimization_types=["linear_programming", "quadratic_programming", "second_order_cone_programming", "semidefinite_programming", "mixed_integer_linear_programming"],
                capabilities=["linear_constraints", "quadratic_constraints", "continuous_variables", "integer_variables", "binary_variables", "convex_optimization", "socp", "sdp"],
                performance_rating=9,
                is_available="MOSEK" in self.available_solvers
            ),
            "XPRESS": SolverInfo(
                name="XPRESS",
                optimization_types=["linear_programming", "quadratic_programming", "mixed_integer_linear_programming", "mixed_integer_quadratic_programming"],
                capabilities=["linear_constraints", "quadratic_constraints", "continuous_variables", "integer_variables", "binary_variables"],
                performance_rating=9,
                is_available="XPRESS" in self.available_solvers
            ),
            
            # Commercial Solvers (if available)
            "GUROBI": SolverInfo(
                name="GUROBI",
                optimization_types=["linear_programming", "quadratic_programming", "mixed_integer_linear_programming", "mixed_integer_quadratic_programming"],
                capabilities=["linear_constraints", "quadratic_constraints", "continuous_variables", "integer_variables", "binary_variables"],
                performance_rating=10,
                is_available="GUROBI" in self.available_solvers
            ),
            "CPLEX": SolverInfo(
                name="CPLEX",
                optimization_types=["linear_programming", "quadratic_programming", "mixed_integer_linear_programming"],
                capabilities=["linear_constraints", "quadratic_constraints", "continuous_variables", "integer_variables", "binary_variables"],
                performance_rating=10,
                is_available="CPLEX" in self.available_solvers
            )
        }
    
    def _detect_available_solvers(self) -> List[str]:
        """Detect which solvers are available on the system."""
        available = []
        
        # Check OR-Tools solvers
        try:
            from ortools.linear_solver import pywraplp
            available.extend(["GLOP", "PDLP", "CBC", "SCIP"])
            logger.info("OR-Tools solvers detected: GLOP, PDLP, CBC, SCIP")
        except ImportError:
            logger.warning("OR-Tools not available")
        
        # Check COIN-OR Solvers
        try:
            import glpk
            available.append("GLPK")
            logger.info("GLPK solver detected")
        except ImportError:
            logger.debug("GLPK not available")
        
        try:
            import clp
            available.append("CLP")
            logger.info("CLP solver detected")
        except ImportError:
            logger.debug("CLP not available")
        
        try:
            import symphony
            available.append("SYMPHONY")
            logger.info("SYMPHONY solver detected")
        except ImportError:
            logger.debug("SYMPHONY not available")
        
        # Check HiGHS
        try:
            import highspy
            available.append("HIGHS")
            logger.info("HiGHS solver detected")
        except ImportError:
            logger.debug("HiGHS not available")
        
        # Check Quadratic Programming Solvers
        try:
            import osqp
            available.append("OSQP")
            logger.info("OSQP solver detected")
        except ImportError:
            logger.debug("OSQP not available")
        
        try:
            import ecos
            available.append("ECOS")
            logger.info("ECOS solver detected")
        except ImportError:
            logger.debug("ECOS not available")
        
        try:
            import cvxopt
            available.append("CVXOPT")
            logger.info("CVXOPT solver detected")
        except ImportError:
            logger.debug("CVXOPT not available")
        
        try:
            import scs
            available.append("SCS")
            logger.info("SCS solver detected")
        except ImportError:
            logger.debug("SCS not available")
        
        # Check CVXPY Ecosystem
        try:
            import cvxpy
            available.append("CVXPY")
            logger.info("CVXPY solver detected")
        except ImportError:
            logger.debug("CVXPY not available")
        
        # Check Specialized Solvers
        try:
            import mosek
            available.append("MOSEK")
            logger.info("MOSEK solver detected")
        except ImportError:
            logger.debug("MOSEK not available")
        
        try:
            import xpress
            available.append("XPRESS")
            logger.info("XPRESS solver detected")
        except ImportError:
            logger.debug("XPRESS not available")
        
        # Check Commercial Solvers
        try:
            import gurobipy
            available.append("GUROBI")
            logger.info("GUROBI solver detected")
        except ImportError:
            logger.debug("GUROBI not available")
        
        try:
            import cplex
            available.append("CPLEX")
            logger.info("CPLEX solver detected")
        except ImportError:
            logger.debug("CPLEX not available")
        
        logger.info(f"Available solvers: {available}")
        return available
    
    def select_solver(
        self, 
        optimization_type: str, 
        problem_size: Optional[Dict[str, Any]] = None,
        performance_requirement: str = "balanced"
    ) -> Dict[str, Any]:
        """
        Select the best available solver for the optimization problem.
        
        Args:
            optimization_type: Type of optimization problem (LP, QP, MILP, etc.)
            problem_size: Dictionary with problem size information
            performance_requirement: "speed", "accuracy", or "balanced"
            
        Returns:
            Dictionary with selected solver information and fallback options
        """
        if problem_size is None:
            problem_size = {}
        
        # Get candidate solvers for this optimization type
        candidates = []
        for solver_name, solver_info in self.solver_database.items():
            if (optimization_type in solver_info.optimization_types and 
                solver_info.is_available):
                candidates.append(solver_info)
        
        if not candidates:
            # No specialized solver available, try fallback
            return self._select_fallback_solver(optimization_type)
        
        # Sort candidates by performance rating
        candidates.sort(key=lambda x: x.performance_rating, reverse=True)
        
        # Select based on performance requirement
        if performance_requirement == "speed":
            # Prefer faster solvers (higher performance rating)
            selected = candidates[0]
        elif performance_requirement == "accuracy":
            # Prefer more accurate solvers (higher performance rating)
            selected = candidates[0]
        else:  # balanced
            # Consider problem size and solver characteristics
            selected = self._select_balanced_solver(candidates, problem_size)
        
        # Get fallback options
        fallbacks = [solver for solver in candidates if solver.name != selected.name]
        
        return {
            "selected_solver": selected.name,
            "optimization_type": optimization_type,
            "capabilities": selected.capabilities,
            "performance_rating": selected.performance_rating,
            "fallback_solvers": [solver.name for solver in fallbacks],
            "reasoning": self._get_selection_reasoning(selected, optimization_type, problem_size)
        }
    
    def _select_balanced_solver(self, candidates: List[SolverInfo], problem_size: Dict[str, Any]) -> SolverInfo:
        """Select solver based on balanced criteria."""
        num_variables = problem_size.get("num_variables", 0)
        num_constraints = problem_size.get("num_constraints", 0)
        
        # For large problems, prefer PDLP or SCIP
        if num_variables > 1000 or num_constraints > 1000:
            for solver in candidates:
                if solver.name in ["PDLP", "SCIP"]:
                    return solver
        
        # For medium problems, prefer GLOP or OSQP
        if num_variables > 100 or num_constraints > 100:
            for solver in candidates:
                if solver.name in ["GLOP", "OSQP"]:
                    return solver
        
        # For small problems, use the highest rated solver
        return candidates[0]
    
    def _select_fallback_solver(self, optimization_type: str) -> Dict[str, Any]:
        """Select fallback solver when no specialized solver is available."""
        fallback_map = {
            "quadratic_programming": {
                "selected_solver": "linear_approximation",
                "optimization_type": "linear_programming",
                "capabilities": ["linear_constraints", "continuous_variables"],
                "performance_rating": 5,
                "fallback_solvers": ["GLOP", "PDLP"],
                "reasoning": "No QP solver available, using linear approximation"
            },
            "mixed_integer_linear_programming": {
                "selected_solver": "linear_programming",
                "optimization_type": "linear_programming",
                "capabilities": ["linear_constraints", "continuous_variables"],
                "performance_rating": 6,
                "fallback_solvers": ["GLOP", "PDLP"],
                "reasoning": "No MILP solver available, relaxing integer constraints"
            },
            "mixed_integer_quadratic_programming": {
                "selected_solver": "linear_approximation",
                "optimization_type": "linear_programming",
                "capabilities": ["linear_constraints", "continuous_variables"],
                "performance_rating": 4,
                "fallback_solvers": ["GLOP", "PDLP"],
                "reasoning": "No MIQP solver available, using linear approximation"
            }
        }
        
        return fallback_map.get(optimization_type, {
            "selected_solver": "GLOP",
            "optimization_type": "linear_programming",
            "capabilities": ["linear_constraints", "continuous_variables"],
            "performance_rating": 7,
            "fallback_solvers": ["PDLP"],
            "reasoning": "Using default linear programming solver"
        })
    
    def _get_selection_reasoning(
        self, 
        selected_solver: SolverInfo, 
        optimization_type: str, 
        problem_size: Dict[str, Any]
    ) -> str:
        """Generate human-readable reasoning for solver selection."""
        num_variables = problem_size.get("num_variables", 0)
        num_constraints = problem_size.get("num_constraints", 0)
        
        reasoning = f"Selected {selected_solver.name} for {optimization_type} problem"
        
        if num_variables > 0 or num_constraints > 0:
            reasoning += f" with {num_variables} variables and {num_constraints} constraints"
        
        reasoning += f" (Performance rating: {selected_solver.performance_rating}/10)"
        
        return reasoning
    
    def get_solver_capabilities(self, solver_name: str) -> Optional[SolverInfo]:
        """Get capabilities of a specific solver."""
        return self.solver_database.get(solver_name)
    
    def list_available_solvers(self) -> List[str]:
        """List all available solvers."""
        return [name for name, info in self.solver_database.items() if info.is_available]
    
    def get_solver_recommendations(self, optimization_type: str) -> Dict[str, Any]:
        """Get solver recommendations for an optimization type."""
        available = self.list_available_solvers()
        suitable = []
        
        for solver_name in available:
            solver_info = self.solver_database[solver_name]
            if optimization_type in solver_info.optimization_types:
                suitable.append({
                    "name": solver_name,
                    "performance_rating": solver_info.performance_rating,
                    "capabilities": solver_info.capabilities
                })
        
        suitable.sort(key=lambda x: x["performance_rating"], reverse=True)
        
        return {
            "optimization_type": optimization_type,
            "recommended_solvers": suitable,
            "total_available": len(available),
            "suitable_count": len(suitable)
        }
