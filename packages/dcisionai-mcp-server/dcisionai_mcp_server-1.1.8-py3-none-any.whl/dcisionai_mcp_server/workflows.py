#!/usr/bin/env python3
"""
DcisionAI Workflow Manager
=========================

Manages industry-specific optimization workflows.
Provides 21 pre-built workflows across 7 industries.
"""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

class WorkflowManager:
    """Manages industry-specific optimization workflows."""
    
    def __init__(self):
        """Initialize the workflow manager."""
        self.workflows = self._load_default_workflows()
    
    def _load_default_workflows(self) -> Dict[str, Any]:
        """Load default workflow templates."""
        return {
            "manufacturing": {
                "production_planning": {
                    "name": "Production Planning Optimization",
                    "description": "Optimize production schedules, resource allocation, and capacity planning",
                    "complexity": "high",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                },
                "inventory_optimization": {
                    "name": "Inventory Optimization",
                    "description": "Minimize inventory costs while maintaining service levels",
                    "complexity": "medium",
                    "estimated_time": "10-20 minutes",
                    "workflows": 3
                },
                "quality_control": {
                    "name": "Quality Control Optimization",
                    "description": "Optimize quality inspection processes and defect detection",
                    "complexity": "medium",
                    "estimated_time": "8-15 minutes",
                    "workflows": 3
                }
            },
            "healthcare": {
                "staff_scheduling": {
                    "name": "Staff Scheduling Optimization",
                    "description": "Optimize healthcare staff schedules and resource allocation",
                    "complexity": "high",
                    "estimated_time": "20-40 minutes",
                    "workflows": 3
                },
                "patient_flow": {
                    "name": "Patient Flow Optimization",
                    "description": "Optimize patient flow through healthcare facilities",
                    "complexity": "medium",
                    "estimated_time": "12-25 minutes",
                    "workflows": 3
                },
                "resource_allocation": {
                    "name": "Resource Allocation Optimization",
                    "description": "Optimize medical equipment and facility resource allocation",
                    "complexity": "high",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                }
            },
            "retail": {
                "demand_forecasting": {
                    "name": "Demand Forecasting Optimization",
                    "description": "Optimize demand forecasting and inventory planning",
                    "complexity": "medium",
                    "estimated_time": "10-20 minutes",
                    "workflows": 3
                },
                "pricing_optimization": {
                    "name": "Pricing Optimization",
                    "description": "Optimize product pricing strategies and promotions",
                    "complexity": "high",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                },
                "supply_chain": {
                    "name": "Supply Chain Optimization",
                    "description": "Optimize retail supply chain and logistics",
                    "complexity": "high",
                    "estimated_time": "20-40 minutes",
                    "workflows": 3
                }
            },
            "marketing": {
                "campaign_optimization": {
                    "name": "Campaign Optimization",
                    "description": "Optimize marketing campaign allocation and targeting",
                    "complexity": "medium",
                    "estimated_time": "12-25 minutes",
                    "workflows": 3
                },
                "budget_allocation": {
                    "name": "Budget Allocation Optimization",
                    "description": "Optimize marketing budget allocation across channels",
                    "complexity": "high",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                },
                "customer_segmentation": {
                    "name": "Customer Segmentation Optimization",
                    "description": "Optimize customer segmentation and targeting strategies",
                    "complexity": "medium",
                    "estimated_time": "10-20 minutes",
                    "workflows": 3
                }
            },
            "financial": {
                "portfolio_optimization": {
                    "name": "Portfolio Optimization",
                    "description": "Optimize investment portfolio allocation and risk management",
                    "complexity": "high",
                    "estimated_time": "20-40 minutes",
                    "workflows": 3
                },
                "risk_assessment": {
                    "name": "Risk Assessment Optimization",
                    "description": "Optimize risk assessment models and credit scoring",
                    "complexity": "high",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                },
                "fraud_detection": {
                    "name": "Fraud Detection Optimization",
                    "description": "Optimize fraud detection algorithms and monitoring",
                    "complexity": "high",
                    "estimated_time": "18-35 minutes",
                    "workflows": 3
                }
            },
            "logistics": {
                "route_optimization": {
                    "name": "Route Optimization",
                    "description": "Optimize delivery routes and transportation logistics",
                    "complexity": "high",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                },
                "warehouse_optimization": {
                    "name": "Warehouse Optimization",
                    "description": "Optimize warehouse operations and storage allocation",
                    "complexity": "medium",
                    "estimated_time": "12-25 minutes",
                    "workflows": 3
                },
                "fleet_management": {
                    "name": "Fleet Management Optimization",
                    "description": "Optimize fleet operations and vehicle allocation",
                    "complexity": "high",
                    "estimated_time": "20-40 minutes",
                    "workflows": 3
                }
            },
            "energy": {
                "grid_optimization": {
                    "name": "Grid Optimization",
                    "description": "Optimize energy grid operations and load balancing",
                    "complexity": "high",
                    "estimated_time": "25-50 minutes",
                    "workflows": 3
                },
                "renewable_integration": {
                    "name": "Renewable Integration Optimization",
                    "description": "Optimize renewable energy integration and storage",
                    "complexity": "high",
                    "estimated_time": "20-40 minutes",
                    "workflows": 3
                },
                "demand_response": {
                    "name": "Demand Response Optimization",
                    "description": "Optimize demand response programs and energy efficiency",
                    "complexity": "medium",
                    "estimated_time": "15-30 minutes",
                    "workflows": 3
                }
            }
        }
    
    def get_all_workflows(self) -> Dict[str, Any]:
        """Get all available workflows organized by industry."""
        return {
            "industries": list(self.workflows.keys()),
            "workflows": self.workflows,
            "total_workflows": sum(
                len(industry_workflows) 
                for industry_workflows in self.workflows.values()
            ),
            "total_industries": len(self.workflows)
        }
    
    def get_industry_workflows(self, industry: str) -> Dict[str, Any]:
        """Get workflows for a specific industry."""
        if industry not in self.workflows:
            return {"error": f"Industry '{industry}' not found"}
        
        return {
            "industry": industry,
            "workflows": self.workflows[industry],
            "workflow_count": len(self.workflows[industry])
        }
    
    def get_workflow_details(self, industry: str, workflow_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific workflow."""
        if industry not in self.workflows:
            return {"error": f"Industry '{industry}' not found"}
        
        if workflow_id not in self.workflows[industry]:
            return {"error": f"Workflow '{workflow_id}' not found in industry '{industry}'"}
        
        workflow = self.workflows[industry][workflow_id]
        return {
            "industry": industry,
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "description": workflow["description"],
            "complexity": workflow["complexity"],
            "estimated_time": workflow["estimated_time"],
            "workflows": workflow["workflows"]
        }
    
    def search_workflows(self, query: str) -> List[Dict[str, Any]]:
        """Search workflows by name or description."""
        results = []
        query_lower = query.lower()
        
        for industry, workflows in self.workflows.items():
            for workflow_id, workflow in workflows.items():
                if (query_lower in workflow["name"].lower() or 
                    query_lower in workflow["description"].lower()):
                    results.append({
                        "industry": industry,
                        "workflow_id": workflow_id,
                        "name": workflow["name"],
                        "description": workflow["description"],
                        "complexity": workflow["complexity"]
                    })
        
        return results
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get statistics about available workflows."""
        total_workflows = sum(
            len(industry_workflows) 
            for industry_workflows in self.workflows.values()
        )
        
        complexity_counts = {"low": 0, "medium": 0, "high": 0}
        for industry_workflows in self.workflows.values():
            for workflow in industry_workflows.values():
                complexity_counts[workflow["complexity"]] += 1
        
        return {
            "total_workflows": total_workflows,
            "total_industries": len(self.workflows),
            "complexity_distribution": complexity_counts,
            "industries": list(self.workflows.keys())
        }
    
    def validate_workflow(self, industry: str, workflow_id: str) -> bool:
        """Validate if a workflow exists."""
        return (industry in self.workflows and 
                workflow_id in self.workflows[industry])
    
    def get_workflow_template(self, industry: str, workflow_id: str) -> Dict[str, Any]:
        """Get a workflow template for execution."""
        if not self.validate_workflow(industry, workflow_id):
            return {"error": "Invalid workflow"}
        
        workflow = self.workflows[industry][workflow_id]
        return {
            "template": {
                "industry": industry,
                "workflow_id": workflow_id,
                "name": workflow["name"],
                "description": workflow["description"],
                "steps": [
                    "Intent Classification",
                    "Data Analysis",
                    "Model Building",
                    "Optimization Solving"
                ],
                "parameters": {
                    "complexity": workflow["complexity"],
                    "estimated_time": workflow["estimated_time"],
                    "workflows": workflow["workflows"]
                }
            }
        }
