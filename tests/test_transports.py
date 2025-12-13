"""Tests for transport implementations."""
import pytest
from mcp_switchboard.transports.launcher import TransportType
from mcp_switchboard.transports.sse_transport import create_sse_app
from mcp_switchboard.transports.http_transport import create_http_app
from mcp.server import Server


def test_create_sse_app():
    """Test SSE app creation."""
    server = Server("test-server")
    app = create_sse_app(server, "/sse")
    
    assert app is not None
    assert len(app.routes) >= 1


@pytest.mark.asyncio
async def test_create_http_app():
    """Test HTTP app creation."""
    server = Server("test-server")
    app = await create_http_app(server, "/mcp")
    
    assert app is not None
    assert len(app.routes) == 1


def test_transport_type_enum():
    """Test TransportType enum."""
    assert TransportType.STDIO.value == "stdio"
    assert TransportType.SSE.value == "sse"
    assert TransportType.HTTP.value == "http"
