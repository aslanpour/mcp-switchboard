"""Example: Complete mcp-switchboard workflow."""
import asyncio
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry
from mcp_switchboard.config.writer import ConfigWriter
from mcp_switchboard.config.models import AgentPlatform
from mcp_switchboard.credentials.manager import CredentialManager
from mcp_switchboard.state.manager import StateManager


async def main():
    """Demonstrate complete workflow."""
    
    # 1. Analyze task
    print("=" * 70)
    print("STEP 1: Task Analysis")
    print("=" * 70)
    
    task = "Deploy ECS service to prod Tokyo using Jira DEVOPS-123"
    print(f"\nTask: {task}\n")
    
    analyzer = TaskAnalyzer()
    analysis = analyzer.analyze(task)
    
    print(f"AWS Account: {analysis.aws_account}")
    print(f"AWS Region: {analysis.aws_region}")
    print(f"Jira Ticket: {analysis.jira_ticket}")
    print(f"Required Services: {', '.join(analysis.required_services)}")
    print(f"Confidence: {analysis.confidence:.2f}")
    
    # 2. Select servers
    print("\n" + "=" * 70)
    print("STEP 2: Server Selection")
    print("=" * 70 + "\n")
    
    registry = ServerRegistry()
    selector = ServerSelector(registry, confidence_threshold=0.7)
    selection = selector.select(analysis)
    
    print("Selected Servers:")
    for server in selection.selected_servers:
        print(f"  • {server.server_name} ({server.confidence:.2f})")
        print(f"    {server.reasoning}")
    
    if selection.rejected_servers:
        print("\nRejected Servers:")
        for server in selection.rejected_servers:
            print(f"  • {server.server_name} ({server.confidence:.2f})")
    
    # 3. Prepare server configurations
    print("\n" + "=" * 70)
    print("STEP 3: Server Configuration")
    print("=" * 70 + "\n")
    
    server_configs = []
    for server_match in selection.selected_servers:
        server_info = registry.get_server(server_match.server_name)
        if server_info:
            config = {
                "name": server_match.server_name,
                "authentication_type": server_info.get("authentication_type", "none"),
                "env": {}
            }
            
            # Add AWS-specific config
            if server_match.server_name == "aws-api-mcp":
                config["env"]["AWS_PROFILE"] = analysis.aws_account or "default"
                config["env"]["AWS_REGION"] = analysis.aws_region or "us-east-1"
            
            server_configs.append(config)
            print(f"Configured: {server_match.server_name}")
    
    # 4. Prepare credentials (dry-run)
    print("\n" + "=" * 70)
    print("STEP 4: Credential Preparation (Dry-run)")
    print("=" * 70 + "\n")
    
    manager = CredentialManager(oauth_automation=False)
    
    for config in server_configs:
        auth_type = config["authentication_type"]
        print(f"{config['name']}: {auth_type}")
        
        if auth_type == "aws_sso":
            print("  → Would check AWS SSO credentials")
            print("  → Would renew if expired")
        elif auth_type == "api_token":
            print("  → Would check token in keychain")
            print("  → Would prompt if missing")
        elif auth_type == "oauth":
            print("  → Would detect OAuth URL")
            print("  → Would open browser if needed")
    
    # 5. Update configuration (dry-run)
    print("\n" + "=" * 70)
    print("STEP 5: Configuration Update (Dry-run)")
    print("=" * 70 + "\n")
    
    print("Would update MCP configuration for: Cursor")
    print(f"Would enable {len(server_configs)} servers")
    print("Would create snapshot for rollback")
    
    # 6. Track in state
    print("\n" + "=" * 70)
    print("STEP 6: State Management")
    print("=" * 70 + "\n")
    
    state = StateManager()
    import time
    task_id = f"example-task-{int(time.time())}"
    state.create_task(
        task_id=task_id,
        task_description=task,
        agent_type="cursor",
        project_path="/path/to/project"
    )
    
    state.update_task(
        task_id=task_id,
        analysis={
            "aws_account": analysis.aws_account,
            "aws_region": analysis.aws_region,
            "jira_ticket": analysis.jira_ticket,
            "confidence": analysis.confidence,
            "selected_servers": [s.server_name for s in selection.selected_servers]
        },
        success=True
    )
    
    print(f"Task tracked: {task_id}")
    print("State saved to database")
    
    # 7. Summary
    print("\n" + "=" * 70)
    print("WORKFLOW COMPLETE")
    print("=" * 70 + "\n")
    
    print("Summary:")
    print(f"  • Task analyzed with {analysis.confidence:.0%} confidence")
    print(f"  • {len(selection.selected_servers)} servers selected")
    print(f"  • {len(server_configs)} servers configured")
    print(f"  • State tracked in database")
    print("\nNext steps:")
    print("  1. Review configuration")
    print("  2. Approve credential renewal")
    print("  3. Apply configuration")
    print("  4. Validate server health")
    print("  5. Begin task execution")


if __name__ == "__main__":
    asyncio.run(main())
