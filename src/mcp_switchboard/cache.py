"""Task fingerprinting and configuration caching."""
from __future__ import annotations
import hashlib
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta


class TaskCache:
    """Cache task configurations based on fingerprints."""
    
    def __init__(self, ttl_hours: int = 24) -> None:
        self.cache: Dict[str, Dict] = {}
        self.ttl = timedelta(hours=ttl_hours)
    
    def generate_fingerprint(self, task_analysis: Dict) -> str:
        """Generate fingerprint from task analysis."""
        # Normalize and hash key attributes
        attributes = {
            "aws_account": task_analysis.get("aws_account"),
            "aws_region": task_analysis.get("aws_region"),
            "capabilities": sorted(task_analysis.get("required_capabilities", [])),
        }
        
        # Create stable hash
        content = json.dumps(attributes, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get(self, fingerprint: str) -> Optional[Dict]:
        """Get cached configuration by fingerprint."""
        if fingerprint not in self.cache:
            return None
        
        entry = self.cache[fingerprint]
        
        # Check if expired
        cached_at = datetime.fromisoformat(entry["cached_at"])
        if datetime.now() - cached_at > self.ttl:
            del self.cache[fingerprint]
            return None
        
        return entry["config"]
    
    def set(self, fingerprint: str, config: Dict) -> None:
        """Cache configuration with fingerprint."""
        self.cache[fingerprint] = {
            "config": config,
            "cached_at": datetime.now().isoformat(),
        }
    
    def clear(self) -> None:
        """Clear all cached entries."""
        self.cache.clear()
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        return {
            "total_entries": len(self.cache),
            "fingerprints": list(self.cache.keys()),
        }
