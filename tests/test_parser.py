"""Tests for task parser."""
import pytest
from mcp_switchboard.analyzer.parser import TaskParser


def test_parse_complete_task():
    """Test parsing a complete task with all information."""
    parser = TaskParser()
    result = parser.parse("Deploy ECS service to prod Tokyo using Jira DEVOPS-123")
    
    assert result.aws_account == "prod"
    assert result.aws_region == "ap-northeast-1"
    assert result.jira_ticket == "DEVOPS-123"
    assert result.jira_project == "DEVOPS"
    assert "aws" in result.mentioned_services
    assert "jira" in result.mentioned_services


def test_parse_aws_account():
    """Test AWS account extraction."""
    parser = TaskParser()
    
    result = parser.parse("Deploy to production")
    assert result.aws_account == "prod"
    
    result = parser.parse("Test in dev environment")
    assert result.aws_account == "dev"
    
    result = parser.parse("Update staging")
    assert result.aws_account == "staging"


def test_parse_aws_region():
    """Test AWS region extraction."""
    parser = TaskParser()
    
    result = parser.parse("Deploy to Tokyo")
    assert result.aws_region == "ap-northeast-1"
    
    result = parser.parse("Update Singapore region")
    assert result.aws_region == "ap-southeast-1"


def test_parse_jira_ticket():
    """Test Jira ticket extraction."""
    parser = TaskParser()
    
    result = parser.parse("Fix bug DEVOPS-456")
    assert result.jira_ticket == "DEVOPS-456"
    assert result.jira_project == "DEVOPS"
    
    result = parser.parse("Implement feature ABC-123")
    assert result.jira_ticket == "ABC-123"


def test_parse_services():
    """Test service identification."""
    parser = TaskParser()
    
    result = parser.parse("Update Terraform infrastructure")
    assert "terraform" in result.mentioned_services
    
    result = parser.parse("Create GitHub PR")
    assert "github" in result.mentioned_services
    
    result = parser.parse("Check CloudWatch logs")
    assert "cloudwatch" in result.mentioned_services


def test_parse_minimal_task():
    """Test parsing task with minimal information."""
    parser = TaskParser()
    result = parser.parse("Write documentation")
    
    assert result.aws_account is None
    assert result.aws_region is None
    assert result.jira_ticket is None
    assert len(result.mentioned_services) == 0
