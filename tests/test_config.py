"""Tests for configuration system."""
import pytest
from pathlib import Path
from mcp_switchboard.config.models import AgentPlatform, MCPServerConfig, SwitchboardConfig
from mcp_switchboard.config.registry import ServerRegistry
from mcp_switchboard.config.agent_detector import detect_agent_platform, get_config_path


def test_agent_platform_enum():
    """Test AgentPlatform enum values."""
    assert AgentPlatform.CURSOR == "cursor"
    assert AgentPlatform.KIRO == "kiro"


def test_mcp_server_config():
    """Test MCPServerConfig model."""
    config = MCPServerConfig(
        name="test-server",
        command="npx",
        args=["-y", "test"],
        capabilities=["test"]
    )
    assert config.name == "test-server"
    assert config.command == "npx"
    assert len(config.args) == 2


def test_switchboard_config_defaults():
    """Test SwitchboardConfig default values."""
    config = SwitchboardConfig()
    assert config.auto_approve is False
    assert config.oauth_automation is False
    assert config.oauth_timeout_seconds == 300


def test_server_registry_load():
    """Test ServerRegistry loads built-in registry."""
    registry = ServerRegistry()
    servers = registry.list_servers()
    assert "atlassian-mcp" in servers
    assert "aws-api-mcp" in servers


def test_server_registry_get_server():
    """Test getting server by name."""
    registry = ServerRegistry()
    server = registry.get_server("atlassian-mcp")
    assert server["name"] == "Atlassian MCP Server"
    assert "jira" in server["capabilities"]


def test_server_registry_by_capability():
    """Test getting servers by capability."""
    registry = ServerRegistry()
    aws_servers = registry.get_servers_by_capability("aws")
    assert "aws-api-mcp" in aws_servers


def test_detect_agent_platform():
    """Test agent platform detection."""
    platform = detect_agent_platform()
    assert isinstance(platform, AgentPlatform)


def test_get_config_path():
    """Test getting config path for agent."""
    path = get_config_path(AgentPlatform.CURSOR)
    assert ".cursor" in str(path)
    assert "mcp.json" in str(path)
