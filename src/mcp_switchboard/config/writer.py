"""Configuration file writer for MCP servers."""
from __future__ import annotations
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .models import AgentPlatform
from .agent_detector import get_config_path


class ConfigWriter:
    """Write MCP server configurations to agent config files."""
    
    def __init__(self, agent: AgentPlatform, scope: str = "user") -> None:
        self.agent = agent
        self.scope = scope
        self.config_path = get_config_path(agent, scope)
        self.snapshot_dir = Path.home() / ".mcp-switchboard" / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
    
    def read_config(self) -> Dict:
        """Read current configuration."""
        if not self.config_path.exists():
            return {"mcpServers": {}}
        
        with open(self.config_path) as f:
            return json.load(f)
    
    def write_config(self, config: Dict) -> None:
        """Write configuration to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, "w") as f:
            json.dump(config, f, indent=2)
    
    def create_snapshot(self) -> str:
        """Create snapshot of current configuration."""
        if not self.config_path.exists():
            return ""
        
        # Ensure snapshot directory exists
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_path = self.snapshot_dir / f"{self.agent.value}_{timestamp}.json"
        
        shutil.copy(self.config_path, snapshot_path)
        
        # Keep only last 10 snapshots
        snapshots = sorted(self.snapshot_dir.glob(f"{self.agent.value}_*.json"))
        for old_snapshot in snapshots[:-10]:
            old_snapshot.unlink()
        
        return str(snapshot_path)
    
    def restore_snapshot(self, snapshot_id: str) -> bool:
        """Restore configuration from snapshot."""
        snapshot_path = Path(snapshot_id)
        
        if not snapshot_path.exists():
            return False
        
        shutil.copy(snapshot_path, self.config_path)
        return True
    
    def update_servers(self, servers: List[Dict]) -> str:
        """Update MCP server configurations."""
        # Create snapshot before changes
        snapshot_id = self.create_snapshot()
        
        # Read current config
        config = self.read_config()
        
        # Update servers
        if "mcpServers" not in config:
            config["mcpServers"] = {}
        
        for server in servers:
            server_name = server.get("name")
            if server_name:
                config["mcpServers"][server_name] = {
                    "command": server.get("command"),
                    "args": server.get("args", []),
                    "env": server.get("env", {}),
                }
        
        # Write updated config
        self.write_config(config)
        
        return snapshot_id
    
    def list_snapshots(self, limit: int = 10) -> List[Dict]:
        """List available snapshots."""
        snapshots = sorted(
            self.snapshot_dir.glob(f"{self.agent.value}_*.json"),
            reverse=True
        )[:limit]
        
        return [
            {
                "id": str(s),
                "timestamp": s.stem.split("_", 1)[1],
                "agent": self.agent.value,
            }
            for s in snapshots
        ]
