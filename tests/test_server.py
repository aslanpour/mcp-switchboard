"""Tests for MCP server."""
import json
import pytest
from mcp_switchboard.server import app, list_tools, call_tool


@pytest.mark.asyncio
async def test_list_tools():
    """Test that tools are listed correctly."""
    tools = await list_tools()
    assert len(tools) == 1
    assert tools[0].name == "setup_mcp_servers"
    assert "task_description" in tools[0].inputSchema["properties"]


@pytest.mark.asyncio
async def test_call_setup_tool():
    """Test calling setup_mcp_servers tool."""
    result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Test task",
            "agent_type": "cursor",
            "project_path": "/test/path",
        },
    )
    
    assert len(result) == 1
    assert result[0].type == "text"
    
    data = json.loads(result[0].text)
    assert data["success"] is True
    assert "configured_servers" in data


@pytest.mark.asyncio
async def test_call_unknown_tool():
    """Test calling unknown tool raises error."""
    with pytest.raises(ValueError, match="Unknown tool"):
        await call_tool("unknown_tool", {})
