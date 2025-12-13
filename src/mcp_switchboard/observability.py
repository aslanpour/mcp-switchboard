"""Observability: structured logging and metrics."""
from __future__ import annotations
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """Structured JSON logger for mcp-switchboard."""
    
    def __init__(self, log_path: Optional[str] = None, level: str = "INFO") -> None:
        self.log_path = Path(log_path).expanduser() if log_path else None
        self.level = getattr(logging, level.upper())
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Setup logger with JSON formatting."""
        self.logger = logging.getLogger("mcp-switchboard")
        self.logger.setLevel(self.level)
        
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            handler = logging.FileHandler(self.log_path)
        else:
            handler = logging.StreamHandler()
        
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
    
    def log(
        self,
        level: str,
        event: str,
        component: str,
        **kwargs: Any
    ) -> None:
        """Log structured event."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.upper(),
            "component": component,
            "event": event,
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(json.dumps(log_entry))
    
    def info(self, event: str, component: str, **kwargs: Any) -> None:
        """Log info event."""
        self.log("INFO", event, component, **kwargs)
    
    def error(self, event: str, component: str, **kwargs: Any) -> None:
        """Log error event."""
        self.log("ERROR", event, component, **kwargs)
    
    def debug(self, event: str, component: str, **kwargs: Any) -> None:
        """Log debug event."""
        self.log("DEBUG", event, component, **kwargs)


class MetricsCollector:
    """Collect and track performance metrics."""
    
    def __init__(self) -> None:
        self.metrics: Dict[str, list] = {}
    
    def record(self, metric_name: str, value: float, tags: Optional[Dict] = None) -> None:
        """Record a metric value."""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        
        self.metrics[metric_name].append({
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "tags": tags or {}
        })
    
    def get_metrics(self, metric_name: Optional[str] = None) -> Dict:
        """Get recorded metrics."""
        if metric_name:
            return {metric_name: self.metrics.get(metric_name, [])}
        return self.metrics
    
    def get_summary(self, metric_name: str) -> Dict:
        """Get summary statistics for a metric."""
        values = [m["value"] for m in self.metrics.get(metric_name, [])]
        
        if not values:
            return {}
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }
