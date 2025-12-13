"""Setup MCP servers tool implementation."""
from __future__ import annotations
from typing import Dict, List, Any
from pydantic import BaseModel
from ..config.registry import ServerRegistry
from ..config.models import AgentPlatform


class SetupRequest(BaseModel):
    """Request to setup MCP servers."""
    task_description: str
    agent_type: str
    project_path: str
    dry_run: bool = False


class SetupResult(BaseModel):
    """Result of MCP server setup."""
    success: bool
    configured_servers: List[Dict[str, Any]]
    ready: bool
    message: str
    decision_report: Dict[str, Any]


class SetupTool:
    """Tool for setting up MCP servers based on task analysis."""
    
    def __init__(self) -> None:
        self.registry = ServerRegistry()
    
    def analyze_task(self, task_description: str) -> Dict[str, Any]:
        """Analyze task description to identify required capabilities."""
        text = task_description.lower()
        
        # Simple keyword-based analysis
        capabilities = []
        if any(kw in text for kw in ["jira", "ticket", "devops-"]):
            capabilities.append("jira")
        if any(kw in text for kw in ["aws", "ec2", "ecs", "lambda", "s3"]):
            capabilities.append("aws")
        if any(kw in text for kw in ["terraform", "tf", "infrastructure"]):
            capabilities.append("terraform")
        if any(kw in text for kw in ["github", "pr", "pull request"]):
            capabilities.append("github")
        
        return {
            "required_capabilities": capabilities,
            "confidence": 0.8 if capabilities else 0.3,
        }
    
    def select_servers(self, analysis: Dict[str, Any]) -> List[str]:
        """Select MCP servers based on task analysis."""
        selected = []
        for capability in analysis["required_capabilities"]:
            servers = self.registry.get_servers_by_capability(capability)
            selected.extend(servers)
        return list(set(selected))  # Remove duplicates
    
    def setup(self, request: SetupRequest) -> SetupResult:
        """Setup MCP servers for the given task."""
        # Analyze task
        analysis = self.analyze_task(request.task_description)
        
        # Select servers
        server_names = self.select_servers(analysis)
        
        # Get server configurations
        configured_servers = []
        for name in server_names:
            server_config = self.registry.get_server(name)
            configured_servers.append({
                "name": name,
                "status": "ready" if not request.dry_run else "dry_run",
                "configuration": server_config,
            })
        
        return SetupResult(
            success=True,
            configured_servers=configured_servers,
            ready=not request.dry_run,
            message=f"Selected {len(configured_servers)} MCP servers based on task analysis",
            decision_report={
                "task_analysis": analysis,
                "selected_servers": server_names,
                "agent_type": request.agent_type,
                "dry_run": request.dry_run,
            },
        )
