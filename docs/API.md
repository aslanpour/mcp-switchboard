# API Documentation

## Core Components

### TaskAnalyzer

Analyzes task descriptions to extract structured information.

```python
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer

analyzer = TaskAnalyzer()
analysis = analyzer.analyze(
    task_description="Deploy ECS to prod Tokyo using DEVOPS-123",
    project_path="/path/to/project"
)

# Returns TaskAnalysis with:
# - aws_account: "prod"
# - aws_region: "ap-northeast-1"
# - jira_ticket: "DEVOPS-123"
# - required_services: ["aws", "jira"]
# - confidence: 0.9
```

### ServerSelector

Selects MCP servers based on task analysis.

```python
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry

registry = ServerRegistry()
selector = ServerSelector(registry, confidence_threshold=0.7)
selection = selector.select(analysis)

# Returns ServerSelection with:
# - selected_servers: List[ServerMatch]
# - rejected_servers: List[ServerMatch]
# - decision_report: Dict
```

### CredentialManager

Manages credentials for MCP servers.

```python
from mcp_switchboard.credentials.manager import CredentialManager

manager = CredentialManager(oauth_automation=False)
results = await manager.prepare_credentials(server_configs)

# Returns Dict[str, bool] - success status per server
```

### ConfigWriter

Manages MCP configuration files.

```python
from mcp_switchboard.config.writer import ConfigWriter
from mcp_switchboard.config.models import AgentPlatform

writer = ConfigWriter(AgentPlatform.CURSOR, scope="user")

# Update servers
snapshot_id = writer.update_servers(servers)

# Rollback if needed
writer.restore_snapshot(snapshot_id)
```

### StateManager

Tracks task history and metrics.

```python
from mcp_switchboard.state.manager import StateManager

state = StateManager()
state.create_task("task-1", "Deploy...", "cursor", "/project")
state.update_task("task-1", analysis=analysis_dict, success=True)

# Query historical patterns
patterns = state.get_historical_patterns(agent_type="cursor", limit=10)
```

## Models

### TaskAnalysis

```python
class TaskAnalysis(BaseModel):
    aws_account: Optional[str]
    aws_region: Optional[str]
    jira_project: Optional[str]
    jira_ticket: Optional[str]
    required_services: List[str]
    required_capabilities: List[str]
    confidence: float
    source: str  # "keyword", "llm", or "hybrid"
```

### ServerMatch

```python
class ServerMatch(BaseModel):
    server_name: str
    confidence: float
    reasoning: str
```

### ServerSelection

```python
class ServerSelection(BaseModel):
    selected_servers: List[ServerMatch]
    rejected_servers: List[ServerMatch]
    decision_report: Dict[str, Any]
```

## Configuration

### Built-in Server Registry

Located at `src/mcp_switchboard/config/registry.yaml`:

```yaml
servers:
  atlassian-mcp:
    capabilities: ["jira", "confluence"]
    authentication_type: "api_token"
  
  aws-api-mcp:
    capabilities: ["aws", "cloud"]
    authentication_type: "aws_sso"
  
  terraform-registry-mcp:
    capabilities: ["terraform", "infrastructure"]
    authentication_type: "none"
  
  github-mcp:
    capabilities: ["github", "git", "pr"]
    authentication_type: "api_token"
```

### Switchboard Configuration

Create `~/.mcp-switchboard/config.yaml`:

```yaml
auto_approve: false
oauth_automation: false
oauth_timeout_seconds: 300
state_database_path: ~/.mcp-switchboard/state.db
log_level: INFO
```

## Examples

### Example 1: Jira + AWS Task

```python
analyzer = TaskAnalyzer()
analysis = analyzer.analyze("Fix bug DEVOPS-456 in prod ECS service")

# Extracts:
# - jira_ticket: "DEVOPS-456"
# - aws_account: "prod"
# - required_services: ["jira", "aws"]

selector = ServerSelector(ServerRegistry())
selection = selector.select(analysis)

# Selects: atlassian-mcp, aws-api-mcp
```

### Example 2: Terraform Infrastructure

```python
analysis = analyzer.analyze("Update Terraform infrastructure for staging")

# Extracts:
# - aws_account: "staging"
# - required_services: ["terraform"]

selection = selector.select(analysis)

# Selects: terraform-registry-mcp
```

### Example 3: Credential Preparation

```python
manager = CredentialManager()

server_configs = [
    {
        "name": "aws-api-mcp",
        "authentication_type": "aws_sso",
        "env": {"AWS_PROFILE": "prod"}
    }
]

results = await manager.prepare_credentials(server_configs)
# Automatically renews AWS SSO if needed
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/mcp_switchboard

# Run specific module
pytest tests/test_analyzer.py -v
```

## Development Status

**Current:** 73% complete, core functionality operational

**Completed:**
- ✅ Task analysis and server selection
- ✅ Credential management
- ✅ Configuration management
- ✅ State tracking
- ✅ Observability

**Requires Python 3.10+ for:**
- MCP SDK integration
- LLM sampling
- Multi-transport support

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

[To be determined]
