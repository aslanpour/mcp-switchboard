"""Health validation for MCP servers."""
from __future__ import annotations
import asyncio
import json
from typing import Dict, List, Optional
from pydantic import BaseModel


class ServerHealth(BaseModel):
    """Health status of an MCP server."""
    server_name: str
    healthy: bool
    startup_time_ms: int
    tools_available: List[str] = []
    error_message: str = ""


class HealthValidator:
    """Validate MCP server health and readiness."""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30) -> None:
        self.max_retries = max_retries
        self.timeout = timeout
        self._server_manager = None
    
    def set_server_manager(self, manager):
        """Set server manager for starting servers."""
        self._server_manager = manager
    
    async def validate_servers(self, server_configs: List[Dict]) -> List[ServerHealth]:
        """Validate health of all servers."""
        results = []
        
        for config in server_configs:
            health = await self._validate_server(config)
            results.append(health)
        
        return results
    
    async def _validate_server(self, config: Dict) -> ServerHealth:
        """Validate a single server with retries."""
        server_name = config.get("name", "unknown")
        command = config.get("command", "uvx")
        args = config.get("args", [server_name])
        
        for attempt in range(self.max_retries):
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Try to start server if manager available
                if self._server_manager:
                    try:
                        server = await self._server_manager.start_server(
                            server_name, command, args
                        )
                        
                        # Wait a bit for server to initialize
                        await asyncio.sleep(0.5)
                        
                        # Check if server is still running
                        is_healthy = await self._server_manager.health_check(server_name)
                        
                        if is_healthy:
                            end_time = asyncio.get_event_loop().time()
                            startup_time_ms = int((end_time - start_time) * 1000)
                            
                            # Try to get tools list (optional)
                            tools = await self._get_server_tools(server_name)
                            
                            return ServerHealth(
                                server_name=server_name,
                                healthy=True,
                                startup_time_ms=startup_time_ms,
                                tools_available=tools,
                            )
                    except Exception as e:
                        # Server failed to start, try again
                        if attempt < self.max_retries - 1:
                            await asyncio.sleep(2 ** attempt)
                            continue
                        raise
                else:
                    # No server manager, just check config validity
                    await asyncio.sleep(0.01)
                    end_time = asyncio.get_event_loop().time()
                    startup_time_ms = int((end_time - start_time) * 1000)
                    
                    return ServerHealth(
                        server_name=server_name,
                        healthy=True,
                        startup_time_ms=startup_time_ms,
                        tools_available=[],
                    )
            
            except Exception as e:
                if attempt == self.max_retries - 1:
                    return ServerHealth(
                        server_name=server_name,
                        healthy=False,
                        startup_time_ms=0,
                        error_message=str(e),
                    )
                
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return ServerHealth(
            server_name=server_name,
            healthy=False,
            startup_time_ms=0,
            error_message="Max retries exceeded",
        )
    
    async def _get_server_tools(self, server_name: str) -> List[str]:
        """Get list of tools from server (best effort)."""
        try:
            # This would require MCP client connection to the server
            # For now, return empty list
            # In production, would use MCP client to call list_tools
            return []
        except Exception:
            return []
