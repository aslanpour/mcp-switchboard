"""Conflict detection for concurrent operations."""
from __future__ import annotations
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class Conflict:
    """Represents a detected conflict."""
    
    def __init__(self, conflict_type: str, message: str, details: Optional[Dict] = None) -> None:
        self.type = conflict_type
        self.message = message
        self.details = details or {}
        self.detected_at = datetime.now()


class ConflictDetector:
    """Detect conflicts in concurrent operations."""
    
    def __init__(self) -> None:
        self.active_operations: Dict[str, Dict] = {}
    
    def register_operation(
        self,
        operation_id: str,
        resource_type: str,
        resource_id: str,
    ) -> None:
        """Register an active operation."""
        self.active_operations[operation_id] = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "started_at": datetime.now().isoformat(),
        }
    
    def unregister_operation(self, operation_id: str) -> None:
        """Unregister completed operation."""
        self.active_operations.pop(operation_id, None)
    
    def detect_conflicts(
        self,
        resource_type: str,
        resource_id: str,
    ) -> List[Conflict]:
        """Detect conflicts for a resource."""
        conflicts = []
        
        for op_id, op_data in self.active_operations.items():
            if (op_data["resource_type"] == resource_type and
                op_data["resource_id"] == resource_id):
                
                conflicts.append(Conflict(
                    conflict_type="resource_in_use",
                    message=f"{resource_type} '{resource_id}' is already in use",
                    details={
                        "operation_id": op_id,
                        "started_at": op_data["started_at"],
                    }
                ))
        
        return conflicts
    
    def cleanup_stale(self, max_age_hours: int = 1) -> int:
        """Clean up stale operations."""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        stale = []
        
        for op_id, op_data in self.active_operations.items():
            started = datetime.fromisoformat(op_data["started_at"])
            if started < cutoff:
                stale.append(op_id)
        
        for op_id in stale:
            self.unregister_operation(op_id)
        
        return len(stale)
