"""State manager for tracking task history and metrics."""
from __future__ import annotations
import sqlite3
import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime


class StateManager:
    """Manage task history and metrics in SQLite database."""
    
    def __init__(self, db_path: str = "~/.mcp-switchboard/state.db") -> None:
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database with schema."""
        schema_path = Path(__file__).parent / "schema.sql"
        conn = sqlite3.connect(self.db_path)
        with open(schema_path) as f:
            conn.executescript(f.read())
        conn.close()
    
    def create_task(
        self,
        task_id: str,
        task_description: str,
        agent_type: str,
        project_path: str,
    ) -> None:
        """Create a new task record."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO tasks (id, task_description, agent_type, project_path) VALUES (?, ?, ?, ?)",
            (task_id, task_description, agent_type, project_path),
        )
        conn.commit()
        conn.close()
    
    def update_task(
        self,
        task_id: str,
        analysis: Optional[Dict[str, Any]] = None,
        selection: Optional[Dict[str, Any]] = None,
        success: Optional[bool] = None,
    ) -> None:
        """Update task with analysis, selection, or completion status."""
        conn = sqlite3.connect(self.db_path)
        updates = []
        params = []
        
        if analysis:
            updates.append("analysis_json = ?")
            params.append(json.dumps(analysis))
        if selection:
            updates.append("selection_json = ?")
            params.append(json.dumps(selection))
        if success is not None:
            updates.append("success = ?")
            params.append(success)
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
        
        if updates:
            params.append(task_id)
            conn.execute(
                f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
        conn.close()
    
    def record_server_usage(
        self,
        task_id: str,
        server_name: str,
        confidence: float,
        success: bool,
        startup_time_ms: int = 0,
    ) -> None:
        """Record server usage for a task."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO server_usage (task_id, server_name, confidence, success, startup_time_ms) VALUES (?, ?, ?, ?, ?)",
            (task_id, server_name, confidence, success, startup_time_ms),
        )
        conn.commit()
        conn.close()
    
    def record_metric(self, task_id: str, metric_name: str, metric_value: float) -> None:
        """Record a metric for a task."""
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            "INSERT INTO metrics (task_id, metric_name, metric_value) VALUES (?, ?, ?)",
            (task_id, metric_name, metric_value),
        )
        conn.commit()
        conn.close()
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_historical_patterns(
        self,
        agent_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get historical successful tasks for pattern learning."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        
        query = "SELECT * FROM tasks WHERE success = 1"
        params: List[Any] = []
        
        if agent_type:
            query += " AND agent_type = ?"
            params.append(agent_type)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor = conn.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
