-- State management schema for mcp-switchboard

CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    task_description TEXT NOT NULL,
    agent_type TEXT NOT NULL,
    project_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    success BOOLEAN,
    analysis_json TEXT,
    selection_json TEXT
);

CREATE TABLE IF NOT EXISTS server_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    server_name TEXT NOT NULL,
    confidence FLOAT,
    success BOOLEAN,
    startup_time_ms INTEGER,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE TABLE IF NOT EXISTS metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id TEXT NOT NULL,
    metric_name TEXT NOT NULL,
    metric_value FLOAT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id)
);

CREATE INDEX IF NOT EXISTS idx_tasks_agent ON tasks(agent_type);
CREATE INDEX IF NOT EXISTS idx_server_usage_task ON server_usage(task_id);
CREATE INDEX IF NOT EXISTS idx_metrics_task ON metrics(task_id);
