"""MCP server implementation for mcp-switchboard."""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry
from mcp_switchboard.credentials.manager import CredentialManager
from mcp_switchboard.config.writer import ConfigWriter
from mcp_switchboard.config.models import AgentPlatform
import json


app = Server("mcp-switchboard")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="setup_mcp_servers",
            description="Analyze task and setup MCP servers automatically",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Natural language task description"
                    },
                    "agent_type": {
                        "type": "string",
                        "enum": ["cursor", "kiro", "claude"],
                        "description": "AI agent platform"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Optional project directory path"
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": "Preview changes without applying"
                    }
                },
                "required": ["task_description", "agent_type"]
            }
        ),
        Tool(
            name="analyze_task",
            description="Analyze task description to extract requirements",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Natural language task description"
                    }
                },
                "required": ["task_description"]
            }
        ),
        Tool(
            name="select_servers",
            description="Select appropriate MCP servers for task",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "Natural language task description"
                    },
                    "confidence_threshold": {
                        "type": "number",
                        "description": "Minimum confidence score (0.0-1.0)"
                    }
                },
                "required": ["task_description"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "analyze_task":
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(arguments["task_description"])
        
        result = {
            "aws_account": analysis.aws_account,
            "aws_region": analysis.aws_region,
            "jira_ticket": analysis.jira_ticket,
            "required_services": analysis.required_services,
            "confidence": analysis.confidence
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "select_servers":
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(arguments["task_description"])
        
        registry = ServerRegistry()
        threshold = arguments.get("confidence_threshold", 0.7)
        selector = ServerSelector(registry, confidence_threshold=threshold)
        selection = selector.select(analysis)
        
        result = {
            "selected_servers": [
                {
                    "name": s.server_name,
                    "confidence": s.confidence,
                    "reasoning": s.reasoning
                }
                for s in selection.selected_servers
            ],
            "rejected_servers": [
                {
                    "name": s.server_name,
                    "confidence": s.confidence
                }
                for s in selection.rejected_servers
            ]
        }
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "setup_mcp_servers":
        # Full orchestration
        task_desc = arguments["task_description"]
        agent_type = arguments["agent_type"]
        dry_run = arguments.get("dry_run", False)
        
        # 1. Analyze task
        analyzer = TaskAnalyzer()
        analysis = analyzer.analyze(task_desc)
        
        # 2. Select servers
        registry = ServerRegistry()
        selector = ServerSelector(registry)
        selection = selector.select(analysis)
        
        # 3. Prepare configurations
        server_configs = []
        for server_match in selection.selected_servers:
            server_info = registry.get_server(server_match.server_name)
            if server_info:
                config = {
                    "name": server_match.server_name,
                    "authentication_type": server_info.get("authentication_type", "none"),
                    "env": {}
                }
                
                if server_match.server_name == "aws-api-mcp" and analysis.aws_account:
                    config["env"]["AWS_PROFILE"] = analysis.aws_account
                    config["env"]["AWS_REGION"] = analysis.aws_region or "us-east-1"
                
                server_configs.append(config)
        
        result = {
            "analysis": {
                "aws_account": analysis.aws_account,
                "aws_region": analysis.aws_region,
                "jira_ticket": analysis.jira_ticket,
                "confidence": analysis.confidence
            },
            "selected_servers": [s.server_name for s in selection.selected_servers],
            "configured_servers": len(server_configs),
            "dry_run": dry_run
        }
        
        if not dry_run:
            result["status"] = "Configuration would be applied (not implemented in dry-run)"
        else:
            result["status"] = "Dry-run complete - no changes made"
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
