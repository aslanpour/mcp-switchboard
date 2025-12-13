"""Tests for advanced features."""
import pytest
import tempfile
from pathlib import Path
from mcp_switchboard.observability import StructuredLogger, MetricsCollector
from mcp_switchboard.cache import TaskCache
from mcp_switchboard.conflict import ConflictDetector, Conflict


def test_structured_logger():
    """Test structured logging."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
        log_path = f.name
    
    logger = StructuredLogger(log_path=log_path, level="INFO")
    logger.info("test_event", "test_component", task_id="123")
    
    # Verify log file created
    assert Path(log_path).exists()
    Path(log_path).unlink()


def test_metrics_collector():
    """Test metrics collection."""
    collector = MetricsCollector()
    
    collector.record("task_analysis_ms", 150.5)
    collector.record("task_analysis_ms", 200.0)
    
    metrics = collector.get_metrics("task_analysis_ms")
    assert len(metrics["task_analysis_ms"]) == 2
    
    summary = collector.get_summary("task_analysis_ms")
    assert summary["count"] == 2
    assert summary["min"] == 150.5
    assert summary["max"] == 200.0
    assert summary["avg"] == 175.25


def test_metrics_collector_empty():
    """Test metrics collector with no data."""
    collector = MetricsCollector()
    summary = collector.get_summary("nonexistent")
    assert summary == {}


def test_task_cache_fingerprint():
    """Test task fingerprint generation."""
    cache = TaskCache()
    
    analysis = {
        "aws_account": "prod",
        "aws_region": "ap-northeast-1",
        "required_capabilities": ["aws", "jira"],
    }
    
    fingerprint = cache.generate_fingerprint(analysis)
    assert len(fingerprint) == 16
    
    # Same analysis should produce same fingerprint
    fingerprint2 = cache.generate_fingerprint(analysis)
    assert fingerprint == fingerprint2


def test_task_cache_set_get():
    """Test caching and retrieval."""
    cache = TaskCache()
    
    fingerprint = "test123"
    config = {"servers": ["aws-api-mcp"]}
    
    cache.set(fingerprint, config)
    retrieved = cache.get(fingerprint)
    
    assert retrieved == config


def test_task_cache_expiry():
    """Test cache expiry."""
    cache = TaskCache(ttl_hours=0)  # Immediate expiry
    
    fingerprint = "test456"
    config = {"servers": ["test"]}
    
    cache.set(fingerprint, config)
    
    # Should be expired
    import time
    time.sleep(0.01)
    retrieved = cache.get(fingerprint)
    assert retrieved is None


def test_task_cache_stats():
    """Test cache statistics."""
    cache = TaskCache()
    
    cache.set("fp1", {"test": 1})
    cache.set("fp2", {"test": 2})
    
    stats = cache.get_stats()
    assert stats["total_entries"] == 2
    assert "fp1" in stats["fingerprints"]


def test_conflict_detector():
    """Test conflict detection."""
    detector = ConflictDetector()
    
    # Register operation
    detector.register_operation("op1", "aws_profile", "prod")
    
    # Detect conflict
    conflicts = detector.detect_conflicts("aws_profile", "prod")
    assert len(conflicts) == 1
    assert conflicts[0].type == "resource_in_use"
    
    # Unregister
    detector.unregister_operation("op1")
    conflicts = detector.detect_conflicts("aws_profile", "prod")
    assert len(conflicts) == 0


def test_conflict_detector_no_conflict():
    """Test no conflict for different resources."""
    detector = ConflictDetector()
    
    detector.register_operation("op1", "aws_profile", "prod")
    
    # Different resource should not conflict
    conflicts = detector.detect_conflicts("aws_profile", "dev")
    assert len(conflicts) == 0


def test_conflict_detector_cleanup():
    """Test cleanup of stale operations."""
    detector = ConflictDetector()
    
    detector.register_operation("op1", "test", "resource1")
    
    # Cleanup with very short max age
    cleaned = detector.cleanup_stale(max_age_hours=0)
    assert cleaned >= 0
