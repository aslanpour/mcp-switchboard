"""Tests for MCP server implementation."""
import pytest
from mcp_switchboard.server import app, list_tools, call_tool


@pytest.mark.asyncio
async def test_list_tools():
    """Test tool listing."""
    tools = await list_tools()
    
    assert len(tools) == 7
    tool_names = [t.name for t in tools]
    assert "setup_mcp_servers" in tool_names
    assert "analyze_task" in tool_names
    assert "select_servers" in tool_names
    assert "manage_servers" in tool_names
    assert "rollback_configuration" in tool_names
    assert "list_snapshots" in tool_names
    assert "get_metrics" in tool_names


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



@pytest.mark.asyncio
async def test_rollback_configuration():
    """Test rollback_configuration tool."""
    import json
    from pathlib import Path
    from mcp_switchboard.config.models import AgentPlatform
    from mcp_switchboard.config.writer import ConfigWriter
    
    # Create a snapshot first
    agent_platform = AgentPlatform.CURSOR
    writer = ConfigWriter(agent_platform, scope="user")
    snapshot_id = writer.update_servers([{
        "name": "test-server",
        "command": "test",
        "args": []
    }])
    
    # Test rollback with specific snapshot
    result = await call_tool(
        "rollback_configuration",
        {"agent_type": "cursor", "snapshot_id": snapshot_id}
    )
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["action"] == "rollback"
    assert data["agent_type"] == "cursor"
    assert data["snapshot_id"] == snapshot_id
    assert data["success"] is True
    
    # Test rollback without snapshot (uses latest)
    result = await call_tool(
        "rollback_configuration",
        {"agent_type": "cursor"}
    )
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["success"] is True


@pytest.mark.asyncio
async def test_list_snapshots():
    """Test list_snapshots tool."""
    import json
    from mcp_switchboard.config.models import AgentPlatform
    from mcp_switchboard.config.writer import ConfigWriter
    
    # Create some snapshots
    agent_platform = AgentPlatform.CURSOR
    writer = ConfigWriter(agent_platform, scope="user")
    writer.update_servers([{"name": "test1", "command": "test1", "args": []}])
    writer.update_servers([{"name": "test2", "command": "test2", "args": []}])
    
    # Test list_snapshots
    result = await call_tool(
        "list_snapshots",
        {"agent_type": "cursor"}
    )
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["agent_type"] == "cursor"
    assert "snapshots" in data
    assert data["count"] >= 2  # At least the 2 we created
    assert isinstance(data["snapshots"], list)
