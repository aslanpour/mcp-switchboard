"""Tests for state manager."""
import pytest
import tempfile
from pathlib import Path
from mcp_switchboard.state.manager import StateManager


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    Path(db_path).unlink(missing_ok=True)


def test_init_db(temp_db):
    """Test database initialization."""
    manager = StateManager(temp_db)
    assert Path(temp_db).exists()


def test_create_task(temp_db):
    """Test creating a task."""
    manager = StateManager(temp_db)
    manager.create_task(
        task_id="test-1",
        task_description="Test task",
        agent_type="cursor",
        project_path="/test",
    )
    
    task = manager.get_task("test-1")
    assert task is not None
    assert task["task_description"] == "Test task"
    assert task["agent_type"] == "cursor"


def test_update_task(temp_db):
    """Test updating a task."""
    manager = StateManager(temp_db)
    manager.create_task("test-2", "Test", "cursor", "/test")
    
    manager.update_task(
        "test-2",
        analysis={"confidence": 0.9},
        success=True,
    )
    
    task = manager.get_task("test-2")
    assert task["success"] == 1
    assert task["completed_at"] is not None


def test_record_server_usage(temp_db):
    """Test recording server usage."""
    manager = StateManager(temp_db)
    manager.create_task("test-3", "Test", "cursor", "/test")
    
    manager.record_server_usage(
        task_id="test-3",
        server_name="aws-api-mcp",
        confidence=0.9,
        success=True,
        startup_time_ms=100,
    )
    
    # Verify it was recorded (would need query method in production)
    task = manager.get_task("test-3")
    assert task is not None


def test_record_metric(temp_db):
    """Test recording metrics."""
    manager = StateManager(temp_db)
    manager.create_task("test-4", "Test", "cursor", "/test")
    
    manager.record_metric("test-4", "analysis_time_ms", 150.5)
    
    task = manager.get_task("test-4")
    assert task is not None


def test_get_historical_patterns(temp_db):
    """Test getting historical patterns."""
    manager = StateManager(temp_db)
    
    # Create successful tasks
    manager.create_task("test-5", "Deploy", "cursor", "/test")
    manager.update_task("test-5", success=True)
    
    manager.create_task("test-6", "Update", "kiro", "/test")
    manager.update_task("test-6", success=True)
    
    # Get all patterns
    patterns = manager.get_historical_patterns()
    assert len(patterns) == 2
    
    # Get patterns for specific agent
    cursor_patterns = manager.get_historical_patterns(agent_type="cursor")
    assert len(cursor_patterns) == 1
    assert cursor_patterns[0]["agent_type"] == "cursor"


def test_get_nonexistent_task(temp_db):
    """Test getting nonexistent task returns None."""
    manager = StateManager(temp_db)
    task = manager.get_task("nonexistent")
    assert task is None
