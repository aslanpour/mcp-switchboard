"""MCP server subprocess lifecycle management."""
import asyncio
import subprocess
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ServerProcess:
    """Running MCP server process."""
    name: str
    process: asyncio.subprocess.Process
    command: str
    args: List[str]
    pid: int
    
    def is_running(self) -> bool:
        """Check if process is still running."""
        return self.process.returncode is None


class ServerManager:
    """Manages MCP server subprocesses."""
    
    def __init__(self):
        self.servers: Dict[str, ServerProcess] = {}
    
    async def start_server(
        self,
        name: str,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None
    ) -> ServerProcess:
        """Start an MCP server subprocess.
        
        Args:
            name: Server identifier
            command: Command to execute
            args: Command arguments
            env: Environment variables
            cwd: Working directory
            
        Returns:
            ServerProcess instance
        """
        if name in self.servers and self.servers[name].is_running():
            return self.servers[name]
        
        args = args or []
        
        # Start subprocess
        process = await asyncio.create_subprocess_exec(
            command,
            *args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            cwd=cwd
        )
        
        server_process = ServerProcess(
            name=name,
            process=process,
            command=command,
            args=args,
            pid=process.pid
        )
        
        self.servers[name] = server_process
        return server_process
    
    async def stop_server(self, name: str, timeout: float = 5.0) -> bool:
        """Stop an MCP server subprocess.
        
        Args:
            name: Server identifier
            timeout: Seconds to wait before force kill
            
        Returns:
            True if stopped successfully
        """
        if name not in self.servers:
            return False
        
        server = self.servers[name]
        
        if not server.is_running():
            del self.servers[name]
            return True
        
        # Try graceful shutdown
        server.process.terminate()
        
        try:
            await asyncio.wait_for(server.process.wait(), timeout=timeout)
        except asyncio.TimeoutError:
            # Force kill
            server.process.kill()
            await server.process.wait()
        
        del self.servers[name]
        return True
    
    async def restart_server(
        self,
        name: str,
        command: Optional[str] = None,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> ServerProcess:
        """Restart an MCP server.
        
        Args:
            name: Server identifier
            command: New command (uses existing if None)
            args: New arguments (uses existing if None)
            env: Environment variables
            
        Returns:
            New ServerProcess instance
        """
        # Get existing config
        if name in self.servers:
            old_server = self.servers[name]
            command = command or old_server.command
            args = args or old_server.args
        
        # Stop existing
        await self.stop_server(name)
        
        # Start new
        return await self.start_server(name, command, args, env)
    
    async def stop_all(self, timeout: float = 5.0):
        """Stop all running servers."""
        tasks = [
            self.stop_server(name, timeout)
            for name in list(self.servers.keys())
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_server(self, name: str) -> Optional[ServerProcess]:
        """Get server process by name."""
        return self.servers.get(name)
    
    def list_servers(self) -> List[str]:
        """List all running server names."""
        return [
            name for name, server in self.servers.items()
            if server.is_running()
        ]
    
    async def health_check(self, name: str) -> bool:
        """Check if server is healthy.
        
        Args:
            name: Server identifier
            
        Returns:
            True if server is running and responsive
        """
        if name not in self.servers:
            return False
        
        server = self.servers[name]
        return server.is_running()
