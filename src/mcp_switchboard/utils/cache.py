"""Simple caching utilities."""
import time
import functools
from typing import Any, Callable, Dict, Tuple


class TTLCache:
    """Time-to-live cache for function results."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[Tuple, Tuple[Any, float]] = {}
    
    def get(self, key: Tuple) -> Any:
        """Get cached value if not expired."""
        if key in self._cache:
            value, timestamp = self._cache[key]
            if time.time() - timestamp < self.ttl_seconds:
                return value
            else:
                del self._cache[key]
        return None
    
    def set(self, key: Tuple, value: Any):
        """Set cached value with current timestamp."""
        self._cache[key] = (value, time.time())
    
    def clear(self):
        """Clear all cached values."""
        self._cache.clear()


def cached(ttl_seconds: int = 300):
    """Decorator to cache function results with TTL."""
    cache = TTLCache(ttl_seconds)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            key = (args, tuple(sorted(kwargs.items())))
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Compute and cache
            result = func(*args, **kwargs)
            cache.set(key, result)
            return result
        
        # Add cache control methods
        wrapper.cache_clear = cache.clear
        wrapper.cache = cache
        
        return wrapper
    
    return decorator
