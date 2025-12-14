"""MCP Prompts for guiding AI agents."""
from typing import List, Dict, Any
from mcp.types import Prompt, PromptArgument, PromptMessage


def get_prompts() -> List[Prompt]:
    """Get all available prompts for AI agents."""
    return [
        # Prompt 1: Setup servers for a task
        Prompt(
            name="setup_for_task",
            description="Automatically configure MCP servers for a specific task",
            arguments=[
                PromptArgument(
                    name="task_description",
                    description="Describe what you want to do (e.g., 'Deploy ECS to prod Tokyo using DEVOPS-123')",
                    required=True
                ),
                PromptArgument(
                    name="agent_type",
                    description="Your AI agent type (cursor, kiro, or claude)",
                    required=True
                )
            ]
        ),
        
        # Prompt 2: Analyze task requirements
        Prompt(
            name="analyze_requirements",
            description="Understand what MCP servers and tools you need for a task",
            arguments=[
                PromptArgument(
                    name="task_description",
                    description="Describe your task",
                    required=True
                )
            ]
        ),
        
        # Prompt 3: Troubleshoot configuration
        Prompt(
            name="troubleshoot_config",
            description="Debug MCP server configuration issues",
            arguments=[
                PromptArgument(
                    name="agent_type",
                    description="Your AI agent type",
                    required=True
                ),
                PromptArgument(
                    name="issue_description",
                    description="What's not working?",
                    required=False
                )
            ]
        ),
        
        # Prompt 4: Rollback configuration
        Prompt(
            name="rollback_changes",
            description="Undo recent MCP configuration changes",
            arguments=[
                PromptArgument(
                    name="agent_type",
                    description="Your AI agent type",
                    required=True
                )
            ]
        ),
        
        # Prompt 5: Optimize performance
        Prompt(
            name="optimize_performance",
            description="Check and optimize MCP server performance",
            arguments=[]
        )
    ]


def get_prompt_messages(prompt_name: str, arguments: Dict[str, str]) -> List[PromptMessage]:
    """Generate prompt messages for AI agent."""
    
    if prompt_name == "setup_for_task":
        task = arguments.get("task_description", "")
        agent = arguments.get("agent_type", "cursor")
        
        return [
            PromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""I need to work on this task: "{task}"

Please help me set up the right MCP servers automatically.

Steps you should take:
1. Call setup_mcp_servers with:
   - task_description: "{task}"
   - agent_type: "{agent}"
   - dry_run: false

2. Wait for the configuration to complete

3. Confirm which servers were configured and that they're healthy

4. Let me know I'm ready to start working!"""
                }
            )
        ]
    
    elif prompt_name == "analyze_requirements":
        task = arguments.get("task_description", "")
        
        return [
            PromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""I'm planning to work on: "{task}"

Before I start, help me understand what I'll need:

1. Call analyze_task with task_description: "{task}"
2. Call select_servers with the same task description
3. Explain:
   - What AWS account/region will be used
   - What MCP servers are recommended
   - Why each server is needed
   - What tools will be available

Don't configure anything yet - just analyze and explain."""
                }
            )
        ]
    
    elif prompt_name == "troubleshoot_config":
        agent = arguments.get("agent_type", "cursor")
        issue = arguments.get("issue_description", "")
        
        return [
            PromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""I'm having issues with my MCP configuration.
Agent: {agent}
{f'Issue: {issue}' if issue else ''}

Please help me troubleshoot:

1. Call list_snapshots for agent_type: "{agent}"
2. Call get_metrics to check performance
3. Check if there are any errors or warnings
4. Suggest what might be wrong
5. Offer to rollback if needed"""
                }
            )
        ]
    
    elif prompt_name == "rollback_changes":
        agent = arguments.get("agent_type", "cursor")
        
        return [
            PromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": f"""I need to undo my recent MCP configuration changes.

Please:
1. Call list_snapshots for agent_type: "{agent}"
2. Show me the available snapshots
3. Call rollback_configuration for agent_type: "{agent}"
4. Confirm the rollback was successful"""
                }
            )
        ]
    
    elif prompt_name == "optimize_performance":
        return [
            PromptMessage(
                role="user",
                content={
                    "type": "text",
                    "text": """Help me optimize mcp-switchboard performance:

1. Call get_metrics to see current performance
2. Analyze the metrics:
   - Task analysis speed
   - Server selection speed
   - Overall orchestration time
3. Tell me if performance is good or if there are issues
4. Suggest optimizations if needed"""
                }
            )
        ]
    
    return []
