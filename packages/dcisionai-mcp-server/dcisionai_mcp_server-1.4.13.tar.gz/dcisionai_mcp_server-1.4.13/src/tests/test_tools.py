#!/usr/bin/env python3
"""
Tests for DcisionAI MCP Tools
============================

Unit tests for the core optimization tools.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from dcisionai_mcp_server.tools import DcisionAITools
from dcisionai_mcp_server.config import Config

class TestDcisionAITools:
    """Test cases for DcisionAITools class."""
    
    @pytest.fixture
    def tools(self):
        """Create a DcisionAITools instance for testing."""
        config = Config(
            gateway_url="https://test-gateway.com/mcp",
            gateway_target="test-target",
            access_token="test-token"
        )
        return DcisionAITools(config)
    
    @pytest.mark.asyncio
    async def test_classify_intent_success(self, tools):
        """Test successful intent classification."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "intent": "optimization",
                    "confidence": 0.95
                }
            }
            mock_post.return_value = mock_response
            
            result = await tools.classify_intent(
                "Optimize our production schedule",
                "manufacturing"
            )
            
            assert result["status"] == "success"
            assert "intent_classification" in result
            assert result["confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_classify_intent_error(self, tools):
        """Test intent classification with error."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            result = await tools.classify_intent(
                "Optimize our production schedule",
                "manufacturing"
            )
            
            assert result["status"] == "error"
            assert "HTTP 500" in result["error"]
            assert result["fallback"] == "Default classification"
    
    @pytest.mark.asyncio
    async def test_analyze_data_success(self, tools):
        """Test successful data analysis."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "data_quality": "high",
                    "features": ["production", "demand", "capacity"]
                }
            }
            mock_post.return_value = mock_response
            
            result = await tools.analyze_data(
                "Production data with 1000 records",
                "tabular",
                "Must maintain quality standards"
            )
            
            assert result["status"] == "success"
            assert "data_analysis" in result
            assert "recommendations" in result
    
    @pytest.mark.asyncio
    async def test_build_model_success(self, tools):
        """Test successful model building."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "model_type": "mixed_integer_programming",
                    "variables": 100,
                    "constraints": 50
                }
            }
            mock_post.return_value = mock_response
            
            result = await tools.build_model(
                "Minimize production costs while meeting demand",
                {"data_quality": "high"},
                "mixed_integer_programming"
            )
            
            assert result["status"] == "success"
            assert "model_specification" in result
            assert result["model_type"] == "mixed_integer_programming"
    
    @pytest.mark.asyncio
    async def test_solve_optimization_success(self, tools):
        """Test successful optimization solving."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "objective_value": 15000,
                    "solution_status": "optimal",
                    "execution_time": 2.5
                }
            }
            mock_post.return_value = mock_response
            
            result = await tools.solve_optimization(
                {"model_type": "mixed_integer_programming"},
                {"time_limit": 300}
            )
            
            assert result["status"] == "success"
            assert "optimization_results" in result
            assert "business_impact" in result
    
    @pytest.mark.asyncio
    async def test_get_workflow_templates_success(self, tools):
        """Test successful workflow templates retrieval."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "industries": ["manufacturing", "healthcare"],
                    "workflows": {}
                }
            }
            mock_post.return_value = mock_response
            
            result = await tools.get_workflow_templates()
            
            assert result["status"] == "success"
            assert "workflow_templates" in result
            assert result["total_workflows"] == 21
    
    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, tools):
        """Test successful workflow execution."""
        with patch.object(tools.client, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "execution_status": "completed",
                    "results": {"cost_savings": 25}
                }
            }
            mock_post.return_value = mock_response
            
            result = await tools.execute_workflow(
                "manufacturing",
                "production_planning",
                {"time_horizon": 30}
            )
            
            assert result["status"] == "success"
            assert "workflow_results" in result
            assert result["industry"] == "manufacturing"
            assert result["workflow_id"] == "production_planning"

class TestWorkflowManager:
    """Test cases for WorkflowManager class."""
    
    def test_get_all_workflows(self):
        """Test getting all workflows."""
        from dcisionai_mcp_server.workflows import WorkflowManager
        
        manager = WorkflowManager()
        workflows = manager.get_all_workflows()
        
        assert "industries" in workflows
        assert "workflows" in workflows
        assert "total_workflows" in workflows
        assert workflows["total_workflows"] == 21
        assert workflows["total_industries"] == 7
    
    def test_get_industry_workflows(self):
        """Test getting workflows for specific industry."""
        from dcisionai_mcp_server.workflows import WorkflowManager
        
        manager = WorkflowManager()
        workflows = manager.get_industry_workflows("manufacturing")
        
        assert workflows["industry"] == "manufacturing"
        assert "workflows" in workflows
        assert workflows["workflow_count"] == 3
    
    def test_get_workflow_details(self):
        """Test getting workflow details."""
        from dcisionai_mcp_server.workflows import WorkflowManager
        
        manager = WorkflowManager()
        details = manager.get_workflow_details("manufacturing", "production_planning")
        
        assert details["industry"] == "manufacturing"
        assert details["workflow_id"] == "production_planning"
        assert "name" in details
        assert "description" in details
        assert "complexity" in details
    
    def test_search_workflows(self):
        """Test searching workflows."""
        from dcisionai_mcp_server.workflows import WorkflowManager
        
        manager = WorkflowManager()
        results = manager.search_workflows("optimization")
        
        assert len(results) > 0
        for result in results:
            assert "industry" in result
            assert "workflow_id" in result
            assert "name" in result
    
    def test_validate_workflow(self):
        """Test workflow validation."""
        from dcisionai_mcp_server.workflows import WorkflowManager
        
        manager = WorkflowManager()
        
        # Valid workflow
        assert manager.validate_workflow("manufacturing", "production_planning") == True
        
        # Invalid industry
        assert manager.validate_workflow("invalid", "production_planning") == False
        
        # Invalid workflow
        assert manager.validate_workflow("manufacturing", "invalid") == False

class TestConfig:
    """Test cases for Config class."""
    
    def test_default_config(self):
        """Test default configuration."""
        from dcisionai_mcp_server.config import Config
        
        config = Config()
        
        assert config.host == "localhost"
        assert config.port == 8000
        assert config.debug == False
        assert config.log_level == "INFO"
    
    def test_config_validation(self):
        """Test configuration validation."""
        from dcisionai_mcp_server.config import Config
        
        # Test missing required fields
        with pytest.raises(ValueError):
            Config(gateway_url="", access_token="")
        
        with pytest.raises(ValueError):
            Config(gateway_target="", access_token="")
        
        with pytest.raises(ValueError):
            Config(gateway_url="test", gateway_target="test", access_token="")
    
    def test_config_to_dict(self):
        """Test configuration to dictionary conversion."""
        from dcisionai_mcp_server.config import Config
        
        config = Config(
            gateway_url="https://test.com",
            gateway_target="test-target",
            access_token="test-token"
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["gateway_url"] == "https://test.com"
        assert config_dict["gateway_target"] == "test-target"
        assert config_dict["access_token"] == "***"  # Token should be hidden
        assert config_dict["host"] == "localhost"
        assert config_dict["port"] == 8000

if __name__ == "__main__":
    pytest.main([__file__])
