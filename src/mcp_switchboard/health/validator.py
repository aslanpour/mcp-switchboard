"""Health validation for MCP servers."""
from __future__ import annotations
import asyncio
from typing import Dict, List
from pydantic import BaseModel


class ServerHealth(BaseModel):
    """Health status of an MCP server."""
    server_name: str
    healthy: bool
    startup_time_ms: int
    error_message: str = ""


class HealthValidator:
    """Validate MCP server health and readiness."""
    
    def __init__(self, max_retries: int = 3, timeout: int = 30) -> None:
        self.max_retries = max_retries
        self.timeout = timeout
    
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
        
        for attempt in range(self.max_retries):
            try:
                start_time = asyncio.get_event_loop().time()
                
                # Simulate server startup check
                # In production, this would actually start the MCP server
                await asyncio.sleep(0.01)  # Minimal delay
                
                end_time = asyncio.get_event_loop().time()
                startup_time_ms = int((end_time - start_time) * 1000)
                
                return ServerHealth(
                    server_name=server_name,
                    healthy=True,
                    startup_time_ms=startup_time_ms,
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
