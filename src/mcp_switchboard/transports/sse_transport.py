"""SSE transport for MCP server."""
from mcp.server.sse import SseServerTransport
from mcp.server import Server
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
import uvicorn


def create_sse_app(server: Server, endpoint: str = "/sse") -> Starlette:
    """Create Starlette app with SSE endpoint.
    
    Args:
        server: MCP Server instance
        endpoint: SSE endpoint path
        
    Returns:
        Starlette application
    """
    sse = SseServerTransport(endpoint)
    
    async def handle_sse(request: Request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options()
            )
    
    async def handle_messages(request: Request):
        async with sse.handle_post_message(
            request.scope,
            request.receive,
            request._send
        ) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options()
            )
    
    app = Starlette(
        routes=[
            Route(endpoint, endpoint=handle_sse, methods=["GET"]),
            Route(f"{endpoint}/message", endpoint=handle_messages, methods=["POST"])
        ]
    )
    
    return app


def run_sse_server(
    server: Server,
    host: str = "0.0.0.0",
    port: int = 8000,
    endpoint: str = "/sse"
):
    """Run MCP server with SSE transport.
    
    Args:
        server: MCP Server instance
        host: Host to bind to
        port: Port to listen on
        endpoint: SSE endpoint path
    """
    import asyncio
    
    async def serve():
        app = await create_sse_app(server, endpoint)
        config = uvicorn.Config(app, host=host, port=port)
        server = uvicorn.Server(config)
        await server.serve()
    
    asyncio.run(serve())
