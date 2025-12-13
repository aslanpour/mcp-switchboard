"""Multi-transport server launcher."""
from mcp.server import Server
from enum import Enum
from typing import Optional


class TransportType(Enum):
    """Supported transport types."""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


async def launch_server(
    server: Server,
    transport: TransportType = TransportType.STDIO,
    host: Optional[str] = None,
    port: Optional[int] = None,
    endpoint: Optional[str] = None
):
    """Launch MCP server with specified transport.
    
    Args:
        server: MCP Server instance
        transport: Transport type to use
        host: Host for network transports
        port: Port for network transports
        endpoint: Endpoint path for network transports
    """
    if transport == TransportType.STDIO:
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    
    elif transport == TransportType.SSE:
        from mcp_switchboard.transports.sse_transport import run_sse_server
        run_sse_server(
            server,
            host=host or "0.0.0.0",
            port=port or 8000,
            endpoint=endpoint or "/sse"
        )
    
    elif transport == TransportType.HTTP:
        from mcp_switchboard.transports.http_transport import run_http_server
        run_http_server(
            server,
            host=host or "0.0.0.0",
            port=port or 8000,
            endpoint=endpoint or "/mcp"
        )
    
    else:
        raise ValueError(f"Unsupported transport: {transport}")
