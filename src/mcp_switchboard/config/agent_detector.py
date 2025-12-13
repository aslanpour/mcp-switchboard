"""Agent platform detection."""
import os
from pathlib import Path
from .models import AgentPlatform


def detect_agent_platform() -> AgentPlatform:
    """Detect which AI agent platform is requesting orchestration."""
    # Check environment variables
    if os.getenv("CURSOR_SESSION_ID"):
        return AgentPlatform.CURSOR
    elif os.getenv("KIRO_SESSION_ID"):
        return AgentPlatform.KIRO
    
    # Check parent process (simplified - would need psutil in production)
    # For now, return CUSTOM as fallback
    return AgentPlatform.CUSTOM


def get_config_path(agent: AgentPlatform, scope: str = "user") -> Path:
    """Get MCP configuration file path for agent."""
    config_dirs = {
        AgentPlatform.CURSOR: ".cursor",
        AgentPlatform.KIRO: ".kiro",
        AgentPlatform.CLAUDE_DESKTOP: "Library/Application Support/Claude",
        AgentPlatform.CLAUDE_CODE: ".claude",
        AgentPlatform.CUSTOM: ".mcp",
    }
    
    base = Path.home() if scope == "user" else Path.cwd()
    return base / config_dirs[agent] / "mcp.json"
