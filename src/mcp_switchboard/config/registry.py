"""MCP server registry loader."""
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import yaml
from .models import MCPServerConfig


class ServerRegistry:
    """Load and manage MCP server registry."""
    
    BUILTIN_REGISTRY = Path(__file__).parent / "registry.yaml"
    
    def __init__(self) -> None:
        self.servers: Dict[str, Dict] = {}
        self._load_builtin()
    
    def _load_builtin(self) -> None:
        """Load built-in server registry."""
        with open(self.BUILTIN_REGISTRY) as f:
            data = yaml.safe_load(f)
        self.servers = data.get("servers", {})
    
    def get_server(self, name: str) -> Dict:
        """Get server configuration by name."""
        return self.servers.get(name, {})
    
    def list_servers(self) -> List[str]:
        """List all available server names."""
        return list(self.servers.keys())
    
    def get_servers_by_capability(self, capability: str) -> List[str]:
        """Get servers that provide a specific capability."""
        return [
            name for name, config in self.servers.items()
            if capability in config.get("capabilities", [])
        ]
