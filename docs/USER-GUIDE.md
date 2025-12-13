# User Guide

## Installation

```bash
pip install -e .
```

## Basic Workflow

### 1. Analyze Your Task

```python
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer

analyzer = TaskAnalyzer()
analysis = analyzer.analyze("Deploy ECS service to prod Tokyo using DEVOPS-123")
```

**What it extracts:**
- AWS account: "prod"
- AWS region: "ap-northeast-1"
- Jira ticket: "DEVOPS-123"
- Required services: ["aws", "jira"]

### 2. Select MCP Servers

```python
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry

registry = ServerRegistry()
selector = ServerSelector(registry)
selection = selector.select(analysis)

for server in selection.selected_servers:
    print(f"{server.server_name}: {server.confidence:.2f} - {server.reasoning}")
```

### 3. Prepare Credentials

```python
from mcp_switchboard.credentials.manager import CredentialManager

manager = CredentialManager()

server_configs = [
    {
        "name": "aws-api-mcp",
        "authentication_type": "aws_sso",
        "env": {"AWS_PROFILE": "prod"}
    }
]

results = await manager.prepare_credentials(server_configs)
```

### 4. Update Configuration

```python
from mcp_switchboard.config.writer import ConfigWriter
from mcp_switchboard.config.models import AgentPlatform

writer = ConfigWriter(AgentPlatform.CURSOR)
snapshot_id = writer.update_servers(server_configs)

print(f"Configuration updated. Snapshot: {snapshot_id}")
```

## Common Use Cases

### Use Case 1: DevOps Task with Jira

**Task:** "Deploy ECS service to prod using DEVOPS-123"

**Result:**
- Selects: `atlassian-mcp`, `aws-api-mcp`
- Configures AWS profile: `prod`
- Prepares Jira credentials

### Use Case 2: Infrastructure Update

**Task:** "Update Terraform infrastructure for staging"

**Result:**
- Selects: `terraform-registry-mcp`
- Configures AWS profile: `staging`

### Use Case 3: GitHub PR Review

**Task:** "Review GitHub PR #456"

**Result:**
- Selects: `github-mcp`
- Prepares GitHub token

## Configuration

### Global Configuration

Create `~/.mcp-switchboard/config.yaml`:

```yaml
auto_approve: false
oauth_automation: false
oauth_timeout_seconds: 300
state_database_path: ~/.mcp-switchboard/state.db
log_level: INFO
```

### Agent-Specific Paths

- **Cursor:** `~/.cursor/mcp.json`
- **Kiro:** `~/.kiro/mcp.json`
- **Claude Desktop:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Claude Code:** `.claude/mcp.json` (project-level)

## Troubleshooting

### Issue: AWS SSO credentials expired

**Solution:**
```python
from mcp_switchboard.credentials.aws_sso import AWSSSOManager

manager = AWSSSOManager()
success = await manager.renew_credentials("prod")
```

### Issue: Token not found

**Solution:**
```python
from mcp_switchboard.credentials.token_store import TokenStore

store = TokenStore()
store.store_token("jira:user@example.com", "your-token")
```

### Issue: Configuration rollback needed

**Solution:**
```python
writer = ConfigWriter(AgentPlatform.CURSOR)
snapshots = writer.list_snapshots()
writer.restore_snapshot(snapshots[0]["id"])
```

## Advanced Features

### Task Caching

```python
from mcp_switchboard.cache import TaskCache

cache = TaskCache(ttl_hours=24)
fingerprint = cache.generate_fingerprint(analysis_dict)

# Check cache
cached_config = cache.get(fingerprint)
if cached_config:
    print("Using cached configuration")
else:
    # Generate new config
    cache.set(fingerprint, new_config)
```

### Conflict Detection

```python
from mcp_switchboard.conflict import ConflictDetector

detector = ConflictDetector()
detector.register_operation("op1", "aws_profile", "prod")

conflicts = detector.detect_conflicts("aws_profile", "prod")
if conflicts:
    print(f"Conflict detected: {conflicts[0].message}")
```

### Observability

```python
from mcp_switchboard.observability import StructuredLogger, MetricsCollector

logger = StructuredLogger(log_path="~/.mcp-switchboard/logs/app.log")
logger.info("server_selected", "selector", server="aws-api-mcp")

metrics = MetricsCollector()
metrics.record("task_analysis_ms", 150.5)
summary = metrics.get_summary("task_analysis_ms")
```

## Best Practices

1. **Always analyze tasks first** before manual configuration
2. **Use dry-run mode** to preview changes
3. **Create snapshots** before major configuration changes
4. **Monitor metrics** to track performance
5. **Review decision reports** to understand server selection

## Support

For issues or questions, create an issue in the repository.
