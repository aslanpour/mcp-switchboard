"""Configuration models for mcp-switchboard."""
from __future__ import annotations
from enum import Enum
from typing import Optional, List, Dict
from pydantic import BaseModel, Field


class AgentPlatform(str, Enum):
    """Supported AI agent platforms."""
    CURSOR = "cursor"
    KIRO = "kiro"
    CLAUDE_DESKTOP = "claude_desktop"
    CLAUDE_CODE = "claude_code"
    CUSTOM = "custom"


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = Field(default_factory=list)
    env: Dict[str, str] = Field(default_factory=dict)
    capabilities: List[str] = Field(default_factory=list)
    authentication_type: Optional[str] = None


class SwitchboardConfig(BaseModel):
    """Main configuration for mcp-switchboard."""
    auto_approve: bool = False
    oauth_automation: bool = False
    oauth_timeout_seconds: int = 300
    state_database_path: str = "~/.mcp-switchboard/state.db"
    log_level: str = "INFO"
