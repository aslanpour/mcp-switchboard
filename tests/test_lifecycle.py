"""Tests for lifecycle management."""
import pytest
import tempfile
import json
from pathlib import Path
from mcp_switchboard.config.models import AgentPlatform
from mcp_switchboard.config.writer import ConfigWriter
from mcp_switchboard.health.validator import HealthValidator
import asyncio


@pytest.fixture
def temp_config_dir():
    """Create temporary config directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_config_writer_read_empty(temp_config_dir):
    """Test reading empty config."""
    writer = ConfigWriter(AgentPlatform.CURSOR)
    writer.config_path = temp_config_dir / "mcp.json"
    
    config = writer.read_config()
    assert config == {"mcpServers": {}}


def test_config_writer_write(temp_config_dir):
    """Test writing config."""
    writer = ConfigWriter(AgentPlatform.CURSOR)
    writer.config_path = temp_config_dir / "mcp.json"
    
    config = {"mcpServers": {"test": {"command": "test"}}}
    writer.write_config(config)
    
    assert writer.config_path.exists()
    with open(writer.config_path) as f:
        saved = json.load(f)
    assert saved == config


def test_config_writer_update_servers(temp_config_dir):
    """Test updating server configurations."""
    writer = ConfigWriter(AgentPlatform.CURSOR)
    writer.config_path = temp_config_dir / "mcp.json"
    writer.snapshot_dir = temp_config_dir / "snapshots"
    
    # Create initial config
    writer.write_config({"mcpServers": {}})
    
    servers = [
        {
            "name": "test-server",
            "command": "npx",
            "args": ["-y", "test"],
            "env": {"KEY": "value"},
        }
    ]
    
    snapshot_id = writer.update_servers(servers)
    assert snapshot_id != ""
    
    config = writer.read_config()
    assert "test-server" in config["mcpServers"]
    assert config["mcpServers"]["test-server"]["command"] == "npx"


def test_config_writer_snapshot(temp_config_dir):
    """Test snapshot creation and restoration."""
    writer = ConfigWriter(AgentPlatform.CURSOR)
    writer.config_path = temp_config_dir / "mcp.json"
    writer.snapshot_dir = temp_config_dir / "snapshots"
    
    # Create initial config
    config = {"mcpServers": {"original": {"command": "test"}}}
    writer.write_config(config)
    
    # Create snapshot
    snapshot_id = writer.create_snapshot()
    assert snapshot_id != ""
    
    # Modify config
    config["mcpServers"]["modified"] = {"command": "new"}
    writer.write_config(config)
    
    # Restore snapshot
    success = writer.restore_snapshot(snapshot_id)
    assert success is True
    
    # Verify restoration
    restored = writer.read_config()
    assert "original" in restored["mcpServers"]
    assert "modified" not in restored["mcpServers"]


def test_config_writer_list_snapshots(temp_config_dir):
    """Test listing snapshots."""
    writer = ConfigWriter(AgentPlatform.CURSOR)
    writer.config_path = temp_config_dir / "mcp.json"
    writer.snapshot_dir = temp_config_dir / "snapshots"
    
    # Create config and snapshots
    writer.write_config({"mcpServers": {}})
    writer.create_snapshot()
    
    snapshots = writer.list_snapshots()
    assert len(snapshots) >= 1
    assert "timestamp" in snapshots[0]


def test_health_validator():
    """Test health validation."""
    validator = HealthValidator()
    
    configs = [
        {"name": "test-server-1"},
        {"name": "test-server-2"},
    ]
    
    results = asyncio.run(validator.validate_servers(configs))
    
    assert len(results) == 2
    assert all(r.healthy for r in results)
    assert all(r.startup_time_ms >= 0 for r in results)


def test_health_validator_single():
    """Test validating single server."""
    validator = HealthValidator()
    
    config = {"name": "test-server"}
    result = asyncio.run(validator._validate_server(config))
    
    assert result.server_name == "test-server"
    assert result.healthy is True
