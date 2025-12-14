"""MCP server implementation for mcp-switchboard."""
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.analyzer.llm_analyzer import LLMTaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry
from mcp_switchboard.credentials.manager import CredentialManager
from mcp_switchboard.config.writer import ConfigWriter
from mcp_switchboard.config.models import AgentPlatform
from mcp_switchboard.lifecycle.server_manager import ServerManager
import json


app = Server("mcp-switchboard")
llm_analyzer = LLMTaskAnalyzer()
server_manager = ServerManager()


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
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": "Use LLM sampling for semantic analysis"
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
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": "Use LLM sampling for semantic analysis"
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
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": "Use LLM sampling for semantic analysis"
                    }
                },
                "required": ["task_description"]
            }
        ),
        Tool(
            name="manage_servers",
            description="Manage MCP server subprocesses (start/stop/restart/list)",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "restart", "list", "health"],
                        "description": "Action to perform"
                    },
                    "server_name": {
                        "type": "string",
                        "description": "Server identifier (required for start/stop/restart/health)"
                    },
                    "command": {
                        "type": "string",
                        "description": "Command to execute (required for start)"
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Command arguments"
                    }
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="rollback_configuration",
            description="Rollback MCP server configuration to previous snapshot",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["cursor", "kiro", "claude"],
                        "description": "AI agent platform"
                    },
                    "snapshot_id": {
                        "type": "string",
                        "description": "Optional snapshot ID to restore (uses latest if not provided)"
                    }
                },
                "required": ["agent_type"]
            }
        ),
        Tool(
            name="list_snapshots",
            description="List available configuration snapshots for rollback",
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["cursor", "kiro", "claude"],
                        "description": "AI agent platform"
                    }
                },
                "required": ["agent_type"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    use_llm = arguments.get("use_llm", False)
    
    if name == "analyze_task":
        task_desc = arguments["task_description"]
        
        if use_llm and hasattr(app, 'request_context'):
            # Use LLM sampling if available
            try:
                llm_result = await llm_analyzer.analyze_with_llm(
                    task_desc,
                    app.request_context.session.create_message
                )
                analysis_dict = {
                    "aws_account": llm_result.aws_account,
                    "aws_region": llm_result.aws_region,
                    "jira_ticket": llm_result.jira_ticket,
                    "required_services": llm_result.required_services,
                    "confidence": llm_result.confidence,
                    "source": llm_result.source
                }
            except Exception as e:
                # Fallback to keyword analysis
                analyzer = TaskAnalyzer()
                analysis = analyzer.analyze(task_desc)
                analysis_dict = {
                    "aws_account": analysis.aws_account,
                    "aws_region": analysis.aws_region,
                    "jira_ticket": analysis.jira_ticket,
                    "required_services": analysis.required_services,
                    "confidence": analysis.confidence,
                    "source": "keyword_fallback",
                    "llm_error": str(e)
                }
        else:
            # Use keyword-based analysis
            analyzer = TaskAnalyzer()
            analysis = analyzer.analyze(task_desc)
            analysis_dict = {
                "aws_account": analysis.aws_account,
                "aws_region": analysis.aws_region,
                "jira_ticket": analysis.jira_ticket,
                "required_services": analysis.required_services,
                "confidence": analysis.confidence,
                "source": "keyword"
            }
        
        return [TextContent(
            type="text",
            text=json.dumps(analysis_dict, indent=2)
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
            # 4. Prepare credentials
            from mcp_switchboard.credentials.manager import CredentialManager
            credential_manager = CredentialManager(oauth_automation=False)
            credential_results = await credential_manager.prepare_credentials(server_configs)
            
            result["credentials"] = {
                name: "ready" if success else "failed"
                for name, success in credential_results.items()
            }
            
            # Note: Continue even if credentials fail (they may not be needed for all operations)
            # User will see credential status in result
            if not all(credential_results.values()):
                result["warnings"] = ["Some credentials failed to prepare - servers may not work correctly"]
            
            # 5. Write configuration
            from mcp_switchboard.config.models import AgentPlatform
            from mcp_switchboard.config.writer import ConfigWriter
            
            agent_platform = AgentPlatform(agent_type)
            writer = ConfigWriter(agent_platform, scope="user")
            
            # Create MCP server configs (list format expected by ConfigWriter)
            mcp_configs = []
            for config in server_configs:
                server_info = registry.get_server(config["name"])
                mcp_config = {
                    "name": config["name"],
                    "command": server_info.get("command", "uvx"),
                    "args": server_info.get("args", [config["name"]]),
                    "env": config.get("env", {})
                }
                mcp_configs.append(mcp_config)
            
            # Update configuration
            snapshot_id = writer.update_servers(mcp_configs)
            
            result["snapshot_id"] = snapshot_id
            result["config_path"] = str(writer.config_path)
            
            # 6. Validate health with real server startup
            from mcp_switchboard.health.validator import HealthValidator
            validator = HealthValidator(max_retries=2, timeout=10)
            validator.set_server_manager(server_manager)
            
            # Validate all configured servers
            health_checks = await validator.validate_servers(server_configs)
            
            result["health"] = {
                check.server_name: {
                    "healthy": check.healthy,
                    "startup_time_ms": check.startup_time_ms,
                    "tools_available": check.tools_available,
                    "error": check.error_message if not check.healthy else None
                }
                for check in health_checks
            }
            
            # Check if any server failed health check
            failed_servers = [c for c in health_checks if not c.healthy]
            if failed_servers:
                result["warnings"] = result.get("warnings", []) + [
                    f"Health check failed for: {', '.join(c.server_name for c in failed_servers)}"
                ]
            
            result["status"] = "success"
        else:
            result["status"] = "Dry-run complete - no changes made"
        
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]
    
    elif name == "manage_servers":
        action = arguments["action"]
        
        if action == "list":
            servers = server_manager.list_servers()
            return [TextContent(
                type="text",
                text=json.dumps({"servers": servers}, indent=2)
            )]
        
        elif action == "start":
            server_name = arguments["server_name"]
            command = arguments["command"]
            args = arguments.get("args", [])
            
            server = await server_manager.start_server(server_name, command, args)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "action": "started",
                    "server": server_name,
                    "pid": server.pid
                }, indent=2)
            )]
        
        elif action == "stop":
            server_name = arguments["server_name"]
            stopped = await server_manager.stop_server(server_name)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "action": "stopped",
                    "server": server_name,
                    "success": stopped
                }, indent=2)
            )]
        
        elif action == "restart":
            server_name = arguments["server_name"]
            server = await server_manager.restart_server(server_name)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "action": "restarted",
                    "server": server_name,
                    "pid": server.pid
                }, indent=2)
            )]
        
        elif action == "health":
            server_name = arguments["server_name"]
            healthy = await server_manager.health_check(server_name)
            return [TextContent(
                type="text",
                text=json.dumps({
                    "server": server_name,
                    "healthy": healthy
                }, indent=2)
            )]
    
    elif name == "rollback_configuration":
        agent_type = arguments["agent_type"]
        snapshot_id = arguments.get("snapshot_id")
        
        from mcp_switchboard.config.models import AgentPlatform
        from mcp_switchboard.config.writer import ConfigWriter
        
        agent_platform = AgentPlatform(agent_type)
        writer = ConfigWriter(agent_platform, scope="user")
        
        if snapshot_id:
            # Restore specific snapshot
            success = writer.restore_snapshot(snapshot_id)
            used_snapshot_id = snapshot_id
        else:
            # Restore latest snapshot
            snapshots = writer.list_snapshots()
            if not snapshots:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": "No snapshots available"}, indent=2)
                )]
            
            latest = snapshots[0]
            success = writer.restore_snapshot(latest["id"])
            used_snapshot_id = latest["id"]
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "action": "rollback",
                "agent_type": agent_type,
                "snapshot_id": used_snapshot_id,
                "success": success,
                "config_path": str(writer.config_path)
            }, indent=2)
        )]
    
    elif name == "list_snapshots":
        agent_type = arguments["agent_type"]
        
        from mcp_switchboard.config.models import AgentPlatform
        from mcp_switchboard.config.writer import ConfigWriter
        
        agent_platform = AgentPlatform(agent_type)
        writer = ConfigWriter(agent_platform, scope="user")
        
        snapshots = writer.list_snapshots()
        
        return [TextContent(
            type="text",
            text=json.dumps({
                "agent_type": agent_type,
                "snapshots": snapshots,
                "count": len(snapshots)
            }, indent=2)
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
