"""Tests for MCP server implementation."""
import pytest
from mcp_switchboard.server import app, list_tools, call_tool


@pytest.mark.asyncio
async def test_list_tools():
    """Test tool listing."""
    tools = await list_tools()
    
    assert len(tools) == 3
    tool_names = [t.name for t in tools]
    assert "setup_mcp_servers" in tool_names
    assert "analyze_task" in tool_names
    assert "select_servers" in tool_names


@pytest.mark.asyncio
async def test_analyze_task_tool():
    """Test analyze_task tool."""
    result = await call_tool(
        "analyze_task",
        {"task_description": "Deploy ECS to prod Tokyo using DEVOPS-123"}
    )
    
    assert len(result) == 1
    assert result[0].type == "text"
    
    import json
    data = json.loads(result[0].text)
    assert data["aws_account"] == "prod"
    assert data["aws_region"] == "ap-northeast-1"
    assert data["jira_ticket"] == "DEVOPS-123"
    assert data["confidence"] > 0.8


@pytest.mark.asyncio
async def test_select_servers_tool():
    """Test select_servers tool."""
    result = await call_tool(
        "select_servers",
        {
            "task_description": "Deploy ECS to prod using DEVOPS-123",
            "confidence_threshold": 0.7
        }
    )
    
    assert len(result) == 1
    
    import json
    data = json.loads(result[0].text)
    assert "selected_servers" in data
    assert len(data["selected_servers"]) > 0
    
    # Should select atlassian and aws servers
    server_names = [s["name"] for s in data["selected_servers"]]
    assert "atlassian-mcp" in server_names
    assert "aws-api-mcp" in server_names


@pytest.mark.asyncio
async def test_setup_mcp_servers_dry_run():
    """Test full setup in dry-run mode."""
    result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy ECS to prod Tokyo using DEVOPS-123",
            "agent_type": "cursor",
            "dry_run": True
        }
    )
    
    assert len(result) == 1
    
    import json
    data = json.loads(result[0].text)
    assert data["analysis"]["aws_account"] == "prod"
    assert data["analysis"]["aws_region"] == "ap-northeast-1"
    assert len(data["selected_servers"]) > 0
    assert data["dry_run"] is True
    assert "Dry-run complete" in data["status"]


@pytest.mark.asyncio
async def test_unknown_tool():
    """Test error handling for unknown tool."""
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("nonexistent_tool", {})
