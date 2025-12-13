"""Tests for LLM-based task analyzer."""
import pytest
from mcp_switchboard.analyzer.llm_analyzer import LLMTaskAnalyzer
from mcp_switchboard.analyzer.parser import ParsedTask


def test_create_analysis_prompt():
    """Test prompt creation."""
    analyzer = LLMTaskAnalyzer()
    prompt = analyzer._create_analysis_prompt("Deploy ECS to prod")
    
    assert "Deploy ECS to prod" in prompt
    assert "JSON" in prompt
    assert "aws_account" in prompt
    assert "jira_ticket" in prompt


def test_analyze_hybrid_no_llm():
    """Test hybrid analysis without LLM result."""
    analyzer = LLMTaskAnalyzer()
    result = analyzer.analyze_hybrid("Deploy ECS to prod Tokyo using DEVOPS-123")
    
    assert result.aws_account == "prod"
    assert result.aws_region == "ap-northeast-1"
    assert result.jira_ticket == "DEVOPS-123"


def test_analyze_hybrid_with_high_confidence_llm():
    """Test hybrid analysis with high confidence LLM result."""
    analyzer = LLMTaskAnalyzer()
    
    llm_result = ParsedTask(
        aws_account="production",
        aws_region="us-west-2",
        jira_ticket="DEVOPS-999",
        required_services=["aws", "jira"],
        confidence=0.95,
        source="llm"
    )
    
    result = analyzer.analyze_hybrid(
        "Deploy ECS to prod Tokyo using DEVOPS-123",
        llm_result
    )
    
    # Should prefer LLM result due to high confidence
    assert result.aws_account == "production"
    assert result.aws_region == "us-west-2"
    assert result.jira_ticket == "DEVOPS-999"
    assert result.source == "hybrid"
    assert result.confidence == 0.95


def test_analyze_hybrid_with_low_confidence_llm():
    """Test hybrid analysis with low confidence LLM result."""
    analyzer = LLMTaskAnalyzer()
    
    llm_result = ParsedTask(
        aws_account="unknown",
        aws_region=None,
        jira_ticket=None,
        required_services=["aws"],
        confidence=0.5,
        source="llm"
    )
    
    result = analyzer.analyze_hybrid(
        "Deploy ECS to prod Tokyo using DEVOPS-123",
        llm_result
    )
    
    # Should prefer keyword parsing due to low LLM confidence
    assert result.aws_account == "prod"
    assert result.aws_region == "ap-northeast-1"
    assert result.jira_ticket == "DEVOPS-123"


def test_analyze_hybrid_merges_services():
    """Test that hybrid analysis merges service lists."""
    analyzer = LLMTaskAnalyzer()
    
    llm_result = ParsedTask(
        aws_account="prod",
        aws_region="ap-northeast-1",
        jira_ticket="DEVOPS-123",
        required_services=["kubernetes", "monitoring"],
        confidence=0.9,
        source="llm"
    )
    
    result = analyzer.analyze_hybrid(
        "Deploy ECS to prod Tokyo using DEVOPS-123",
        llm_result
    )
    
    # Should keep LLM services due to high confidence
    assert "kubernetes" in result.required_services
    assert "monitoring" in result.required_services
    assert result.source == "hybrid"
    assert result.confidence == 0.9
