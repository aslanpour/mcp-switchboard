"""Tests for server selector."""
import pytest
from mcp_switchboard.config.registry import ServerRegistry
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector


def test_select_servers_jira_aws():
    """Test selecting servers for Jira and AWS task."""
    registry = ServerRegistry()
    analyzer = TaskAnalyzer()
    selector = ServerSelector(registry)
    
    analysis = analyzer.analyze("Deploy ECS to prod using DEVOPS-123")
    result = selector.select(analysis)
    
    selected_names = [s.server_name for s in result.selected_servers]
    assert "atlassian-mcp" in selected_names
    assert "aws-api-mcp" in selected_names


def test_select_servers_terraform():
    """Test selecting servers for Terraform task."""
    registry = ServerRegistry()
    analyzer = TaskAnalyzer()
    selector = ServerSelector(registry)
    
    analysis = analyzer.analyze("Update Terraform infrastructure")
    result = selector.select(analysis)
    
    selected_names = [s.server_name for s in result.selected_servers]
    assert "terraform-registry-mcp" in selected_names


def test_confidence_threshold():
    """Test confidence threshold filtering."""
    registry = ServerRegistry()
    analyzer = TaskAnalyzer()
    selector = ServerSelector(registry, confidence_threshold=0.9)
    
    analysis = analyzer.analyze("Deploy something")
    result = selector.select(analysis)
    
    # High threshold should result in fewer selections
    assert len(result.selected_servers) <= 2


def test_no_matches():
    """Test task with no matching servers."""
    registry = ServerRegistry()
    analyzer = TaskAnalyzer()
    selector = ServerSelector(registry)
    
    analysis = analyzer.analyze("Write documentation")
    result = selector.select(analysis)
    
    assert len(result.selected_servers) == 0


def test_decision_report():
    """Test decision report generation."""
    registry = ServerRegistry()
    analyzer = TaskAnalyzer()
    selector = ServerSelector(registry)
    
    analysis = analyzer.analyze("Deploy with Terraform")
    result = selector.select(analysis)
    
    assert "task_analysis" in result.decision_report
    assert "selected_count" in result.decision_report
    assert result.decision_report["threshold"] == 0.7
