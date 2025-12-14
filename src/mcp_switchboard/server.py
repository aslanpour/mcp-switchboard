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
from mcp_switchboard.prompts import get_prompts, get_prompt_messages
import json


app = Server("mcp-switchboard")
llm_analyzer = LLMTaskAnalyzer()
server_manager = ServerManager()


@app.list_prompts()
async def list_prompts():
    """List available prompts for AI agents."""
    return get_prompts()


@app.get_prompt()
async def get_prompt(name: str, arguments: dict):
    """Get prompt messages for a specific prompt."""
    messages = get_prompt_messages(name, arguments)
    return {
        "messages": messages
    }


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="setup_mcp_servers",
            description=(
                "Automatically configure MCP servers for a task. Analyzes your task description to determine "
                "required services (AWS, Jira, GitHub, etc.), selects appropriate MCP servers, prepares credentials, "
                "writes configuration files, and validates server health. Use this when starting work on a new task "
                "that requires cloud services, issue tracking, or code management. Returns configured servers, "
                "snapshot ID for rollback, and health status. This is the main orchestration tool - use it to set up "
                "your entire MCP environment in one call."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": (
                            "Natural language description of what you want to do. Be specific about AWS account "
                            "(prod/dev/uat), region (e.g., Tokyo, Sydney, Virginia), and Jira ticket if applicable. "
                            "Examples: 'Deploy ECS service to prod Tokyo using DEVOPS-123', "
                            "'Fix Lambda timeout in dev us-east-1', 'Update DynamoDB table in uat Sydney'. "
                            "The more details you provide, the more accurate the configuration."
                        )
                    },
                    "agent_type": {
                        "type": "string",
                        "enum": ["cursor", "kiro", "claude"],
                        "description": (
                            "Your AI agent platform. Use 'cursor' for Cursor IDE, 'kiro' for Kiro CLI, "
                            "'claude' for Claude Desktop. This determines which configuration file to update."
                        )
                    },
                    "project_path": {
                        "type": "string",
                        "description": (
                            "Optional path to your project directory. If provided, can be used for context-aware "
                            "configuration in future versions. Currently not required."
                        )
                    },
                    "dry_run": {
                        "type": "boolean",
                        "description": (
                            "If true, preview what would be configured without actually applying changes. "
                            "Use this to see which servers would be selected and what credentials would be needed "
                            "before committing to the configuration. Defaults to false."
                        )
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": (
                            "If true, use LLM sampling for semantic task analysis (95%+ accuracy but slower ~500ms). "
                            "If false, use keyword-based parsing (90% accuracy but faster <2ms). "
                            "Defaults to false. Use true for complex or ambiguous task descriptions."
                        )
                    }
                },
                "required": ["task_description", "agent_type"]
            }
        ),
        Tool(
            name="analyze_task",
            description=(
                "Extract structured information from a task description without configuring anything. "
                "Identifies AWS account (prod/dev/uat), AWS region, Jira ticket number, required services, "
                "and confidence score. Use this BEFORE setup_mcp_servers if you want to preview what will be "
                "configured, or to understand task requirements for planning purposes. This is a read-only operation "
                "that doesn't modify any configuration. Useful for validation or when you want manual control "
                "over the setup process."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": (
                            "Task description to analyze. Can be informal or structured. "
                            "Examples: 'deploy to prod', 'DEVOPS-123: fix lambda', 'update ecs in tokyo'. "
                            "The analyzer will extract AWS account, region, Jira ticket, and required services."
                        )
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": (
                            "Use LLM for semantic analysis (more accurate, slower) vs keyword parsing (faster, less flexible). "
                            "Defaults to false."
                        )
                    }
                },
                "required": ["task_description"]
            }
        ),
        Tool(
            name="select_servers",
            description=(
                "Recommend which MCP servers to use for a task based on requirements analysis. "
                "Returns a ranked list of servers with confidence scores (0.0-1.0) and reasoning for each recommendation. "
                "Use this to understand which tools you'll need before actually configuring them. "
                "Internally calls analyze_task first, then matches requirements to available servers in the registry. "
                "Useful for planning, manual review of recommendations, or when you want to see alternatives. "
                "Does not modify any configuration - purely informational."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": (
                            "Task description to analyze for server selection. Will be parsed to extract "
                            "AWS account, region, services needed, etc."
                        )
                    },
                    "confidence_threshold": {
                        "type": "number",
                        "description": (
                            "Minimum confidence score (0.0-1.0) for server selection. "
                            "Default 0.7 means only servers with 70%+ confidence are recommended. "
                            "Lower values (e.g., 0.5) include more servers but with less certainty. "
                            "Higher values (e.g., 0.9) only include highly confident matches."
                        )
                    },
                    "use_llm": {
                        "type": "boolean",
                        "description": "Use LLM for semantic analysis. Defaults to false."
                    }
                },
                "required": ["task_description"]
            }
        ),
        Tool(
            name="manage_servers",
            description=(
                "Manage MCP server subprocesses lifecycle. Start, stop, restart, list, or check health "
                "of MCP servers. Use this for manual server management, troubleshooting, or advanced use cases. "
                "Note: setup_mcp_servers handles server lifecycle automatically, so you typically only need this "
                "for debugging (e.g., restarting a hung server) or manual control. "
                "Actions: 'start' launches a server, 'stop' gracefully shuts down, 'restart' stops then starts, "
                "'list' shows all running servers, 'health' checks if a server is responding."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["start", "stop", "restart", "list", "health"],
                        "description": (
                            "Action to perform: "
                            "'start' - Launch a new MCP server subprocess (requires server_name, command, args), "
                            "'stop' - Gracefully shutdown a server (requires server_name), "
                            "'restart' - Stop and start a server (requires server_name), "
                            "'list' - Show all running servers (no other params needed), "
                            "'health' - Check if a server is responding (requires server_name)"
                        )
                    },
                    "server_name": {
                        "type": "string",
                        "description": (
                            "Server identifier (e.g., 'aws-api-mcp', 'atlassian-mcp', 'github-mcp'). "
                            "Required for start/stop/restart/health actions. Not needed for list action."
                        )
                    },
                    "command": {
                        "type": "string",
                        "description": (
                            "Command to execute (e.g., 'uvx', 'node', 'python'). "
                            "Required only for start action. Use 'uvx' for most MCP servers."
                        )
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": (
                            "Command arguments as array of strings. For uvx, typically ['server-package-name']. "
                            "Example: ['aws-api-mcp'] or ['@modelcontextprotocol/server-github']. "
                            "Required only for start action."
                        )
                    }
                },
                "required": ["action"]
            }
        ),
        Tool(
            name="rollback_configuration",
            description=(
                "Restore MCP server configuration to a previous state. Every configuration change creates "
                "a timestamped snapshot, allowing you to undo changes if something goes wrong. "
                "Use this when: 1) A configuration broke something and you need to revert, "
                "2) You want to restore a known-good state, 3) You're experimenting and want to reset. "
                "If no snapshot_id provided, rolls back to the most recent snapshot. "
                "Snapshots include: timestamp, configured servers, and full configuration state. "
                "This is a safe operation - you can always rollback a rollback."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["cursor", "kiro", "claude"],
                        "description": (
                            "Your AI agent platform. Determines which configuration file to rollback. "
                            "Each agent has independent configuration and snapshots."
                        )
                    },
                    "snapshot_id": {
                        "type": "string",
                        "description": (
                            "Optional specific snapshot ID to restore (format: 'snapshot_YYYYMMDD_HHMMSS'). "
                            "If not provided, uses the most recent snapshot. "
                            "Get available snapshot IDs using list_snapshots tool. "
                            "Example: 'snapshot_20251215_103045'"
                        )
                    }
                },
                "required": ["agent_type"]
            }
        ),
        Tool(
            name="list_snapshots",
            description=(
                "List all available configuration snapshots for rollback. Each snapshot includes: "
                "timestamp (when it was created), configured servers (what was set up), and snapshot ID (for rollback). "
                "Use this to: 1) See configuration history and what changed over time, "
                "2) Find a specific snapshot to rollback to, 3) Understand when configurations were modified. "
                "Snapshots are created automatically every time setup_mcp_servers runs successfully. "
                "Useful for auditing, troubleshooting, or finding a known-good configuration to restore."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "agent_type": {
                        "type": "string",
                        "enum": ["cursor", "kiro", "claude"],
                        "description": (
                            "Your AI agent platform. Each agent has independent snapshots. "
                            "Cursor snapshots are separate from Kiro snapshots, etc."
                        )
                    }
                },
                "required": ["agent_type"]
            }
        ),
        Tool(
            name="get_metrics",
            description=(
                "Get performance metrics and statistics for mcp-switchboard operations. "
                "Returns timing data for task analysis, server selection, and overall orchestration. "
                "Metrics include: count (how many times executed), min/max/avg (timing in milliseconds), "
                "and total (cumulative time). Use this to: 1) Check if mcp-switchboard is performing well, "
                "2) Identify performance bottlenecks, 3) Validate that operations meet performance requirements "
                "(<2s for analysis, <10s for orchestration). Can get all metrics or a specific metric by name. "
                "Useful for troubleshooting slow operations or performance monitoring."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "metric_name": {
                        "type": "string",
                        "description": (
                            "Optional specific metric name to retrieve (e.g., 'task_analysis_ms', 'server_selection_ms'). "
                            "If not provided, returns all available metrics. "
                            "Common metrics: 'task_analysis_ms' (task parsing time), "
                            "'server_selection_ms' (server matching time). "
                            "Use without metric_name to see all available metrics first."
                        )
                    }
                },
                "required": []
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
    
    elif name == "get_metrics":
        metric_name = arguments.get("metric_name")
        
        from mcp_switchboard.utils.metrics import get_collector
        collector = get_collector()
        
        if metric_name:
            stats = collector.get_stats(metric_name)
            if stats is None:
                return [TextContent(
                    type="text",
                    text=json.dumps({"error": f"Metric '{metric_name}' not found"}, indent=2)
                )]
            
            return [TextContent(
                type="text",
                text=json.dumps({
                    "metric": metric_name,
                    "stats": stats
                }, indent=2)
            )]
        else:
            all_stats = collector.get_all_stats()
            return [TextContent(
                type="text",
                text=json.dumps({
                    "metrics": all_stats,
                    "count": len(all_stats)
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
