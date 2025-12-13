"""Tests for server subprocess manager."""
import pytest
import asyncio
from mcp_switchboard.lifecycle.server_manager import ServerManager


@pytest.mark.asyncio
async def test_start_server():
    """Test starting a server subprocess."""
    manager = ServerManager()
    
    # Start a simple echo process
    server = await manager.start_server(
        "test-server",
        "python",
        ["-c", "import time; time.sleep(1)"]
    )
    
    assert server.name == "test-server"
    assert server.is_running()
    assert server.pid > 0
    
    # Cleanup
    await manager.stop_server("test-server")


@pytest.mark.asyncio
async def test_stop_server():
    """Test stopping a server subprocess."""
    manager = ServerManager()
    
    server = await manager.start_server(
        "test-server",
        "python",
        ["-c", "import time; time.sleep(10)"]
    )
    
    assert server.is_running()
    
    # Stop server
    stopped = await manager.stop_server("test-server")
    assert stopped is True
    assert "test-server" not in manager.servers


@pytest.mark.asyncio
async def test_restart_server():
    """Test restarting a server."""
    manager = ServerManager()
    
    server1 = await manager.start_server(
        "test-server",
        "python",
        ["-c", "import time; time.sleep(1)"]
    )
    pid1 = server1.pid
    
    # Restart
    server2 = await manager.restart_server("test-server")
    pid2 = server2.pid
    
    assert pid1 != pid2
    assert server2.is_running()
    
    # Cleanup
    await manager.stop_server("test-server")


@pytest.mark.asyncio
async def test_list_servers():
    """Test listing running servers."""
    manager = ServerManager()
    
    await manager.start_server("server1", "python", ["-c", "import time; time.sleep(1)"])
    await manager.start_server("server2", "python", ["-c", "import time; time.sleep(1)"])
    
    servers = manager.list_servers()
    assert "server1" in servers
    assert "server2" in servers
    
    # Cleanup
    await manager.stop_all()


@pytest.mark.asyncio
async def test_stop_all():
    """Test stopping all servers."""
    manager = ServerManager()
    
    await manager.start_server("server1", "python", ["-c", "import time; time.sleep(1)"])
    await manager.start_server("server2", "python", ["-c", "import time; time.sleep(1)"])
    
    await manager.stop_all()
    
    assert len(manager.servers) == 0


@pytest.mark.asyncio
async def test_health_check():
    """Test server health check."""
    manager = ServerManager()
    
    server = await manager.start_server(
        "test-server",
        "python",
        ["-c", "import time; time.sleep(1)"]
    )
    
    # Should be healthy
    healthy = await manager.health_check("test-server")
    assert healthy is True
    
    # Stop and check again
    await manager.stop_server("test-server")
    healthy = await manager.health_check("test-server")
    assert healthy is False


@pytest.mark.asyncio
async def test_start_duplicate_server():
    """Test starting server with duplicate name returns existing."""
    manager = ServerManager()
    
    server1 = await manager.start_server(
        "test-server",
        "python",
        ["-c", "import time; time.sleep(1)"]
    )
    
    # Try to start again with same name
    server2 = await manager.start_server(
        "test-server",
        "python",
        ["-c", "import time; time.sleep(1)"]
    )
    
    # Should return same server
    assert server1.pid == server2.pid
    
    # Cleanup
    await manager.stop_server("test-server")
