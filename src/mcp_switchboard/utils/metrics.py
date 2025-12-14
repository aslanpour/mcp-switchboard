"""Performance metrics collection."""
import time
import functools
from typing import Dict, List, Optional
from collections import defaultdict


class MetricsCollector:
    """Collect and aggregate performance metrics."""
    
    def __init__(self):
        self._metrics: Dict[str, List[float]] = defaultdict(list)
    
    def record(self, metric_name: str, value: float):
        """Record a metric value."""
        self._metrics[metric_name].append(value)
    
    def get_stats(self, metric_name: str) -> Optional[Dict[str, float]]:
        """Get statistics for a metric."""
        values = self._metrics.get(metric_name, [])
        if not values:
            return None
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "total": sum(values)
        }
    
    def get_all_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all metrics."""
        return {
            name: self.get_stats(name)
            for name in self._metrics.keys()
        }
    
    def clear(self):
        """Clear all metrics."""
        self._metrics.clear()


# Global metrics collector
_collector = MetricsCollector()


def get_collector() -> MetricsCollector:
    """Get the global metrics collector."""
    return _collector


def timed(metric_name: str):
    """Decorator to time function execution and record metric."""
    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return await func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000  # ms
                _collector.record(metric_name, duration)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = (time.perf_counter() - start) * 1000  # ms
                _collector.record(metric_name, duration)
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
