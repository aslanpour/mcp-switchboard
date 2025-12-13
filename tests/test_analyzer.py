"""Tests for task analyzer."""
import pytest
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer


def test_analyze_complete_task():
    """Test analyzing a complete task."""
    analyzer = TaskAnalyzer()
    result = analyzer.analyze("Deploy ECS to prod Tokyo using DEVOPS-123")
    
    assert result.aws_account == "prod"
    assert result.aws_region == "ap-northeast-1"
    assert result.jira_ticket == "DEVOPS-123"
    assert "aws" in result.required_services
    assert "jira" in result.required_services
    assert result.confidence > 0.7
    assert result.source == "keyword"


def test_analyze_partial_task():
    """Test analyzing task with partial information."""
    analyzer = TaskAnalyzer()
    result = analyzer.analyze("Update Terraform infrastructure")
    
    assert "terraform" in result.required_services
    assert result.confidence >= 0.3


def test_analyze_minimal_task():
    """Test analyzing minimal task."""
    analyzer = TaskAnalyzer()
    result = analyzer.analyze("Write documentation")
    
    assert len(result.required_services) == 0
    assert result.confidence == 0.3  # Baseline


def test_confidence_calculation():
    """Test confidence score increases with more information."""
    analyzer = TaskAnalyzer()
    
    minimal = analyzer.analyze("Do something")
    partial = analyzer.analyze("Deploy to prod")
    complete = analyzer.analyze("Deploy ECS to prod Tokyo using DEVOPS-123")
    
    assert minimal.confidence < partial.confidence < complete.confidence
