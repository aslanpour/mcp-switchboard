# MCP Client Configuration

## Using mcp-switchboard with MCP Clients

### Cursor

Add to `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "switchboard": {
      "command": "uvx",
      "args": ["mcp-switchboard-server"]
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "switchboard": {
      "command": "uvx",
      "args": ["mcp-switchboard-server"]
    }
  }
}
```

### Kiro

Add to `~/.kiro/mcp.json`:

```json
{
  "mcpServers": {
    "switchboard": {
      "command": "uvx",
      "args": ["mcp-switchboard-server"]
    }
  }
}
```

### Custom MCP Client

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

server_params = StdioServerParameters(
    command="uvx",
    args=["mcp-switchboard-server"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Call tools
        result = await session.call_tool(
            "analyze_task",
            arguments={"task_description": "Deploy ECS to prod"}
        )
```

## Available Tools

### 1. setup_mcp_servers

Full orchestration workflow - analyzes task, selects servers, prepares configuration.

**Parameters:**
- `task_description` (string, required): Natural language task description
- `agent_type` (string, required): One of "cursor", "kiro", "claude"
- `project_path` (string, optional): Project directory path
- `dry_run` (boolean, optional): Preview changes without applying

**Example:**
```json
{
  "task_description": "Deploy ECS service to prod Tokyo using DEVOPS-123",
  "agent_type": "cursor",
  "dry_run": true
}
```

**Response:**
```json
{
  "analysis": {
    "aws_account": "prod",
    "aws_region": "ap-northeast-1",
    "jira_ticket": "DEVOPS-123",
    "confidence": 0.9
  },
  "selected_servers": ["atlassian-mcp", "aws-api-mcp"],
  "configured_servers": 2,
  "dry_run": true,
  "status": "Dry-run complete - no changes made"
}
```

### 2. analyze_task

Analyzes task description to extract structured information.

**Parameters:**
- `task_description` (string, required): Natural language task description

**Example:**
```json
{
  "task_description": "Fix bug DEVOPS-456 in staging environment"
}
```

**Response:**
```json
{
  "aws_account": "staging",
  "aws_region": null,
  "jira_ticket": "DEVOPS-456",
  "required_services": ["jira", "aws"],
  "confidence": 0.85
}
```

### 3. select_servers

Selects appropriate MCP servers based on task requirements.

**Parameters:**
- `task_description` (string, required): Natural language task description
- `confidence_threshold` (number, optional): Minimum confidence score (0.0-1.0), default: 0.7

**Example:**
```json
{
  "task_description": "Update Terraform infrastructure",
  "confidence_threshold": 0.8
}
```

**Response:**
```json
{
  "selected_servers": [
    {
      "name": "terraform-registry-mcp",
      "confidence": 0.85,
      "reasoning": "Provides capabilities: terraform"
    }
  ],
  "rejected_servers": []
}
```

## Using with uv/uvx

### Advantages of uvx

- **No installation required**: Runs directly from PyPI
- **Automatic updates**: Always uses latest version
- **Isolated environment**: No dependency conflicts
- **Fast startup**: uv's optimized package resolution

### Alternative: Local Installation

If you prefer a local installation:

```bash
# Install once
uv pip install mcp-switchboard

# Then use installed command
{
  "mcpServers": {
    "switchboard": {
      "command": "mcp-switchboard-server"
    }
  }
}
```

## Troubleshooting

### Server not starting

Check if uvx is installed:
```bash
which uvx
uvx --version
```

Install uv if needed:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Tool calls failing

Test the server manually:
```bash
uvx mcp-switchboard-server
# Should start and wait for input
```

### Debugging

Enable debug logging in your MCP client configuration:
```json
{
  "mcpServers": {
    "switchboard": {
      "command": "uvx",
      "args": ["mcp-switchboard-server"],
      "env": {
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Performance

- **Startup time**: ~1-2 seconds with uvx
- **Tool execution**: <100ms for analysis and selection
- **Memory usage**: ~50MB

## Security

- No credentials stored in MCP server
- All credential operations delegated to system keychain
- State database stored locally in `~/.mcp-switchboard/`
