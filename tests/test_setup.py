"""Tests for setup tool."""
import pytest
from mcp_switchboard.tools.setup import SetupTool, SetupRequest


def test_analyze_task_jira():
    """Test task analysis identifies Jira requirement."""
    tool = SetupTool()
    analysis = tool.analyze_task("Deploy ECS to prod Tokyo using Jira DEVOPS-123")
    assert "jira" in analysis["required_capabilities"]
    assert "aws" in analysis["required_capabilities"]


def test_analyze_task_terraform():
    """Test task analysis identifies Terraform requirement."""
    tool = SetupTool()
    analysis = tool.analyze_task("Update terraform infrastructure for staging")
    assert "terraform" in analysis["required_capabilities"]


def test_select_servers():
    """Test server selection based on capabilities."""
    tool = SetupTool()
    analysis = {"required_capabilities": ["jira", "aws"]}
    servers = tool.select_servers(analysis)
    assert "atlassian-mcp" in servers
    assert "aws-api-mcp" in servers


def test_setup_basic():
    """Test basic setup flow."""
    tool = SetupTool()
    request = SetupRequest(
        task_description="Deploy ECS using Jira DEVOPS-123",
        agent_type="cursor",
        project_path="/test/path",
    )
    result = tool.setup(request)
    
    assert result.success is True
    assert len(result.configured_servers) > 0
    assert result.ready is True


def test_setup_dry_run():
    """Test setup in dry-run mode."""
    tool = SetupTool()
    request = SetupRequest(
        task_description="Deploy with Terraform",
        agent_type="cursor",
        project_path="/test/path",
        dry_run=True,
    )
    result = tool.setup(request)
    
    assert result.success is True
    assert result.ready is False
    assert result.decision_report["dry_run"] is True


def test_setup_no_matches():
    """Test setup with task that matches no servers."""
    tool = SetupTool()
    request = SetupRequest(
        task_description="Write documentation",
        agent_type="cursor",
        project_path="/test/path",
    )
    result = tool.setup(request)
    
    assert result.success is True
    assert len(result.configured_servers) == 0
