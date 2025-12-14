"""End-to-end integration tests."""
import pytest
import json
from pathlib import Path
from mcp_switchboard.server import call_tool


@pytest.mark.asyncio
async def test_full_orchestration_workflow():
    """Test complete setup_mcp_servers workflow."""
    
    # 1. Setup with dry_run=False
    result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy ECS to prod Tokyo using DEVOPS-123",
            "agent_type": "cursor",
            "dry_run": False
        }
    )
    
    data = json.loads(result[0].text)
    
    # 2. Verify analysis
    assert data["analysis"]["aws_account"] == "prod"
    assert data["analysis"]["aws_region"] == "ap-northeast-1"
    assert data["analysis"]["jira_ticket"] == "DEVOPS-123"
    
    # 3. Verify servers selected
    assert "atlassian-mcp" in data["selected_servers"]
    assert "aws-api-mcp" in data["selected_servers"]
    
    # 4. Verify config written
    assert "snapshot_id" in data
    assert "config_path" in data
    assert data["status"] == "success"
    
    # 5. Verify credentials prepared
    assert "credentials" in data
    assert isinstance(data["credentials"], dict)
    
    # 6. Verify health checked
    assert "health" in data
    assert isinstance(data["health"], dict)
    
    # 7. Verify config file exists
    config_path = Path(data["config_path"])
    assert config_path.exists()
    
    # 8. Test list_snapshots
    snapshots_result = await call_tool(
        "list_snapshots",
        {"agent_type": "cursor"}
    )
    
    snapshots_data = json.loads(snapshots_result[0].text)
    assert snapshots_data["count"] >= 1
    assert any(s["id"] == data["snapshot_id"] for s in snapshots_data["snapshots"])
    
    # 9. Test rollback
    rollback_result = await call_tool(
        "rollback_configuration",
        {
            "agent_type": "cursor",
            "snapshot_id": data["snapshot_id"]
        }
    )
    
    rollback_data = json.loads(rollback_result[0].text)
    assert rollback_data["success"] is True
    assert rollback_data["snapshot_id"] == data["snapshot_id"]


@pytest.mark.asyncio
async def test_orchestration_performance():
    """Test that orchestration completes in reasonable time."""
    import time
    
    start = time.time()
    
    result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy ECS to prod",
            "agent_type": "cursor",
            "dry_run": False
        }
    )
    
    duration = time.time() - start
    
    # Requirement: <10 seconds (excluding credential renewal)
    # In practice, should be much faster (~1-2 seconds)
    assert duration < 10.0, f"Orchestration took {duration:.2f}s, expected <10s"
    
    data = json.loads(result[0].text)
    assert data["status"] == "success"


@pytest.mark.asyncio
async def test_multi_agent_isolation():
    """Test that different agents have isolated configurations."""
    
    # Setup for cursor
    cursor_result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy ECS to prod",
            "agent_type": "cursor",
            "dry_run": False
        }
    )
    
    cursor_data = json.loads(cursor_result[0].text)
    cursor_snapshot = cursor_data["snapshot_id"]
    cursor_config_path = cursor_data["config_path"]
    
    # Setup for kiro
    kiro_result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy Lambda to dev",
            "agent_type": "kiro",
            "dry_run": False
        }
    )
    
    kiro_data = json.loads(kiro_result[0].text)
    kiro_snapshot = kiro_data["snapshot_id"]
    kiro_config_path = kiro_data["config_path"]
    
    # Verify different snapshots
    assert cursor_snapshot != kiro_snapshot
    
    # Verify different config paths
    assert cursor_config_path != kiro_config_path
    
    # Verify both config files exist
    assert Path(cursor_config_path).exists()
    assert Path(kiro_config_path).exists()
    
    # Verify config paths contain agent names
    assert "cursor" in cursor_config_path.lower() or "Cursor" in cursor_config_path
    assert "kiro" in kiro_config_path.lower() or "Kiro" in kiro_config_path


@pytest.mark.asyncio
async def test_error_handling():
    """Test error handling in orchestration."""
    
    # Test with invalid agent type (should fail validation before reaching handler)
    with pytest.raises(Exception):
        await call_tool(
            "setup_mcp_servers",
            {
                "task_description": "Deploy ECS",
                "agent_type": "invalid_agent",
                "dry_run": False
            }
        )
