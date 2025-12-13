"""HTTP transport for MCP server."""
from mcp.server import Server
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn
import json


async def create_http_app(server: Server, endpoint: str = "/mcp") -> Starlette:
    """Create Starlette app with HTTP endpoint.
    
    Args:
        server: MCP Server instance
        endpoint: HTTP endpoint path
        
    Returns:
        Starlette application
    """
    async def handle_request(request: Request):
        """Handle HTTP POST requests."""
        try:
            body = await request.json()
            
            # Simple HTTP-based MCP protocol
            # In production, this would use proper MCP HTTP transport
            method = body.get("method")
            params = body.get("params", {})
            
            if method == "tools/list":
                tools = await server._list_tools_handler()
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {"tools": [t.model_dump() for t in tools]}
                })
            
            elif method == "tools/call":
                name = params.get("name")
                arguments = params.get("arguments", {})
                result = await server._call_tool_handler(name, arguments)
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "result": {"content": [c.model_dump() for c in result]}
                })
            
            else:
                return JSONResponse({
                    "jsonrpc": "2.0",
                    "id": body.get("id"),
                    "error": {"code": -32601, "message": "Method not found"}
                }, status_code=404)
        
        except Exception as e:
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": body.get("id") if hasattr(body, "get") else None,
                "error": {"code": -32603, "message": str(e)}
            }, status_code=500)
    
    app = Starlette(
        routes=[
            Route(endpoint, endpoint=handle_request, methods=["POST"])
        ]
    )
    
    return app


def run_http_server(
    server: Server,
    host: str = "0.0.0.0",
    port: int = 8000,
    endpoint: str = "/mcp"
):
    """Run MCP server with HTTP transport.
    
    Args:
        server: MCP Server instance
        host: Host to bind to
        port: Port to listen on
        endpoint: HTTP endpoint path
    """
    import asyncio
    
    async def serve():
        app = await create_http_app(server, endpoint)
        config = uvicorn.Config(app, host=host, port=port)
        server_instance = uvicorn.Server(config)
        await server_instance.serve()
    
    asyncio.run(serve())
