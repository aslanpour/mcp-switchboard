# Missing Requirements Implementation Plan

**Status:** CRITICAL - Core functionality not implemented  
**Priority:** P0 - Blocks production use  
**Estimated Time:** 2-3 hours  
**Current Completion:** 30-40% functional (85% components exist)

---

## 🚨 CRITICAL GAPS SUMMARY

### What We Have (Components)
- ✅ Task analysis (keyword + LLM)
- ✅ Server selection with confidence
- ✅ Credential managers (AWS SSO, OAuth, tokens)
- ✅ Configuration writer with snapshots
- ✅ Health validator
- ✅ State management
- ✅ MCP server with 4 tools
- ✅ Multi-transport (STDIO/SSE/HTTP)

### What's Missing (Integration)
- ❌ setup_mcp_servers actually working
- ❌ Credential renewal in workflow
- ❌ Health validation in workflow
- ❌ Configuration rollback tool
- ❌ End-to-end orchestration
- ❌ Success criteria validation
- ❌ Performance benchmarks

---

## 📋 IMPLEMENTATION TASKS

### TASK 1: Implement Full setup_mcp_servers Orchestration (60 min)

**Objective:** Make setup_mcp_servers actually configure MCP servers

**Current State:**
```python
# src/mcp_switchboard/server.py line 214-260
# Returns: "Configuration would be applied (not implemented)"
# Does NOT call ConfigWriter, CredentialManager, or HealthValidator
```

**Required Changes:**

**Step 1.1: Integrate ConfigWriter (15 min)**
```python
# In setup_mcp_servers handler, after preparing server_configs:

if not dry_run:
    # Write configuration
    from mcp_switchboard.config.models import AgentPlatform
    
    agent_platform = AgentPlatform(agent_type)
    writer = ConfigWriter(agent_platform, scope="user")
    
    # Create MCP server configs
    mcp_configs = []
    for config in server_configs:
        mcp_config = {
            "command": "uvx",  # or from registry
            "args": [config["name"]],
            "env": config.get("env", {})
        }
        mcp_configs.append((config["name"], mcp_config))
    
    # Update configuration
    snapshot_id = writer.update_servers(dict(mcp_configs))
    
    result["snapshot_id"] = snapshot_id
    result["config_path"] = str(writer.config_path)
```

**Step 1.2: Integrate CredentialManager (20 min)**
```python
# Before writing config, prepare credentials:

from mcp_switchboard.credentials.manager import CredentialManager

credential_manager = CredentialManager(oauth_automation=False)
credential_results = await credential_manager.prepare_credentials(server_configs)

result["credentials"] = {
    name: "ready" if success else "failed"
    for name, success in credential_results.items()
}

# If any credential failed, return error
if not all(credential_results.values()):
    result["status"] = "error"
    result["error"] = "Credential preparation failed"
    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

**Step 1.3: Integrate HealthValidator (15 min)**
```python
# After writing config, validate servers:

from mcp_switchboard.health.validator import HealthValidator

validator = HealthValidator()
health_results = {}

for server_name in [s.server_name for s in selection.selected_servers]:
    # For now, just check if config was written
    # In production, would actually start server and check
    health_results[server_name] = "configured"

result["health"] = health_results
result["status"] = "success"
```

**Step 1.4: Update Response (10 min)**
```python
result = {
    "analysis": {...},
    "selected_servers": [...],
    "configured_servers": len(server_configs),
    "snapshot_id": snapshot_id,
    "config_path": str(writer.config_path),
    "credentials": credential_results,
    "health": health_results,
    "status": "success",
    "dry_run": False
}
```

**Acceptance Criteria:**
- [ ] setup_mcp_servers with dry_run=False actually writes config
- [ ] Credentials are prepared before config write
- [ ] Health validation runs after config write
- [ ] Returns snapshot_id for rollback
- [ ] Returns detailed status for each step

---

### TASK 2: Implement rollback_configuration Tool (30 min)

**Objective:** Add MCP tool to rollback configuration changes

**Step 2.1: Add Tool Definition (10 min)**
```python
# In list_tools(), add:

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
)
```

**Step 2.2: Implement Handler (15 min)**
```python
# In call_tool(), add:

elif name == "rollback_configuration":
    agent_type = arguments["agent_type"]
    snapshot_id = arguments.get("snapshot_id")
    
    from mcp_switchboard.config.models import AgentPlatform
    
    agent_platform = AgentPlatform(agent_type)
    writer = ConfigWriter(agent_platform, scope="user")
    
    if snapshot_id:
        # Restore specific snapshot
        success = writer.restore_snapshot(snapshot_id)
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
    
    return [TextContent(
        type="text",
        text=json.dumps({
            "action": "rollback",
            "agent_type": agent_type,
            "snapshot_id": snapshot_id or latest["id"],
            "success": success,
            "config_path": str(writer.config_path)
        }, indent=2)
    )]
```

**Step 2.3: Add Tests (5 min)**
```python
# tests/test_mcp_server.py

@pytest.mark.asyncio
async def test_rollback_configuration():
    """Test rollback_configuration tool."""
    # Create a snapshot first
    writer = ConfigWriter(AgentPlatform.CURSOR)
    snapshot_id = writer.update_servers({"test": {"command": "test"}})
    
    # Test rollback
    result = await call_tool(
        "rollback_configuration",
        {"agent_type": "cursor", "snapshot_id": snapshot_id}
    )
    
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert data["success"] is True
```

**Acceptance Criteria:**
- [ ] rollback_configuration tool defined
- [ ] Can rollback to specific snapshot
- [ ] Can rollback to latest snapshot
- [ ] Returns success/failure status
- [ ] Test passes

---

### TASK 3: Add list_snapshots Tool (15 min)

**Objective:** Allow users to see available snapshots

**Step 3.1: Add Tool (5 min)**
```python
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
```

**Step 3.2: Implement Handler (10 min)**
```python
elif name == "list_snapshots":
    agent_type = arguments["agent_type"]
    
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
```

**Acceptance Criteria:**
- [ ] list_snapshots tool defined
- [ ] Returns list of snapshots with timestamps
- [ ] Works for all agent types

---

### TASK 4: End-to-End Integration Test (30 min)

**Objective:** Validate complete workflow works

**Step 4.1: Create Integration Test (20 min)**
```python
# tests/test_integration.py

@pytest.mark.asyncio
async def test_full_orchestration_workflow():
    """Test complete setup_mcp_servers workflow."""
    
    # 1. Setup
    result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy ECS to prod Tokyo using DEVOPS-123",
            "agent_type": "cursor",
            "dry_run": False
        }
    )
    
    data = json.loads(result[0].text)
    
    # 2. Verify analysis
    assert data["analysis"]["aws_account"] == "prod"
    assert data["analysis"]["aws_region"] == "ap-northeast-1"
    
    # 3. Verify servers selected
    assert "atlassian-mcp" in data["selected_servers"]
    assert "aws-api-mcp" in data["selected_servers"]
    
    # 4. Verify config written
    assert "snapshot_id" in data
    assert "config_path" in data
    assert data["status"] == "success"
    
    # 5. Verify config file exists
    config_path = Path(data["config_path"])
    assert config_path.exists()
    
    # 6. Test rollback
    rollback_result = await call_tool(
        "rollback_configuration",
        {
            "agent_type": "cursor",
            "snapshot_id": data["snapshot_id"]
        }
    )
    
    rollback_data = json.loads(rollback_result[0].text)
    assert rollback_data["success"] is True
```

**Step 4.2: Create Performance Test (10 min)**
```python
@pytest.mark.asyncio
async def test_orchestration_performance():
    """Test that orchestration completes in <10 seconds."""
    import time
    
    start = time.time()
    
    result = await call_tool(
        "setup_mcp_servers",
        {
            "task_description": "Deploy ECS to prod",
            "agent_type": "cursor",
            "dry_run": False
        }
    )
    
    duration = time.time() - start
    
    # Requirement: <10 seconds (excluding credential renewal)
    assert duration < 10.0, f"Orchestration took {duration}s, expected <10s"
```

**Acceptance Criteria:**
- [ ] Full workflow test passes
- [ ] Performance test passes (<10s)
- [ ] Config file actually created
- [ ] Rollback works

---

### TASK 5: Update Documentation (20 min)

**Objective:** Document the working functionality

**Step 5.1: Update README (10 min)**
```markdown
## Usage

### Complete Task Setup

```python
# Automatically configure MCP servers for a task
result = await session.call_tool(
    "setup_mcp_servers",
    arguments={
        "task_description": "Deploy ECS to prod Tokyo using DEVOPS-123",
        "agent_type": "cursor",
        "dry_run": False  # Set to True to preview
    }
)

# Result includes:
# - analysis: Extracted task requirements
# - selected_servers: Chosen MCP servers
# - snapshot_id: For rollback
# - credentials: Credential status
# - health: Server health status
```

### Rollback Configuration

```python
# Rollback to previous configuration
result = await session.call_tool(
    "rollback_configuration",
    arguments={
        "agent_type": "cursor"
    }
)
```
```

**Step 5.2: Update API.md (10 min)**
- Document setup_mcp_servers with dry_run=False
- Document rollback_configuration
- Document list_snapshots
- Add integration examples

**Acceptance Criteria:**
- [ ] README updated with working examples
- [ ] API.md has complete tool documentation
- [ ] Examples are tested and work

---

### TASK 6: Success Criteria Validation (30 min)

**Objective:** Measure and validate all success criteria

**Step 6.1: Accuracy Measurement (15 min)**
```python
# tests/test_accuracy.py

def test_task_analysis_accuracy():
    """Measure task analysis accuracy on test dataset."""
    
    test_cases = [
        {
            "task": "Deploy ECS to prod Tokyo using DEVOPS-123",
            "expected": {
                "aws_account": "prod",
                "aws_region": "ap-northeast-1",
                "jira_ticket": "DEVOPS-123"
            }
        },
        # Add 20+ test cases
    ]
    
    analyzer = TaskAnalyzer()
    correct = 0
    total = len(test_cases)
    
    for case in test_cases:
        analysis = analyzer.analyze(case["task"])
        if (analysis.aws_account == case["expected"]["aws_account"] and
            analysis.aws_region == case["expected"]["aws_region"] and
            analysis.jira_ticket == case["expected"]["jira_ticket"]):
            correct += 1
    
    accuracy = correct / total
    assert accuracy >= 0.95, f"Accuracy {accuracy:.2%} < 95%"
```

**Step 6.2: Performance Validation (15 min)**
```python
def test_performance_criteria():
    """Validate all performance requirements."""
    
    # Task analysis <2s
    start = time.time()
    analyzer.analyze("Deploy ECS to prod")
    assert time.time() - start < 2.0
    
    # Server selection <500ms
    start = time.time()
    selector.select(analysis)
    assert time.time() - start < 0.5
```

**Acceptance Criteria:**
- [ ] Accuracy measured on 20+ test cases
- [ ] Accuracy ≥95%
- [ ] All performance criteria validated
- [ ] Tests pass

---

## 📊 IMPLEMENTATION CHECKLIST

### Phase 1: Core Integration (90 min)
- [ ] Task 1: Implement full setup_mcp_servers (60 min)
  - [ ] Step 1.1: ConfigWriter integration
  - [ ] Step 1.2: CredentialManager integration
  - [ ] Step 1.3: HealthValidator integration
  - [ ] Step 1.4: Response update
- [ ] Task 2: Implement rollback_configuration (30 min)
  - [ ] Step 2.1: Tool definition
  - [ ] Step 2.2: Handler implementation
  - [ ] Step 2.3: Tests

### Phase 2: Additional Tools (15 min)
- [ ] Task 3: Add list_snapshots tool (15 min)

### Phase 3: Validation (60 min)
- [ ] Task 4: End-to-end integration test (30 min)
- [ ] Task 5: Update documentation (20 min)
- [ ] Task 6: Success criteria validation (30 min)

### Total Estimated Time: 2.75 hours

---

## 🎯 SUCCESS CRITERIA

### Functional Requirements
- [ ] setup_mcp_servers with dry_run=False writes actual config
- [ ] Credentials are renewed before config write
- [ ] Health validation runs after config write
- [ ] rollback_configuration restores previous state
- [ ] list_snapshots shows available snapshots
- [ ] Multi-agent isolation works (different configs per agent)

### Performance Requirements
- [ ] Task analysis completes in <2 seconds
- [ ] Server selection completes in <500ms
- [ ] Total orchestration completes in <10 seconds
- [ ] Credential renewal completes in <60 seconds

### Quality Requirements
- [ ] All integration tests pass
- [ ] Accuracy ≥95% on test dataset
- [ ] Documentation complete and accurate
- [ ] Zero critical bugs

---

## 🚀 EXECUTION PLAN

### Step-by-Step Implementation

1. **Start with Task 1** (setup_mcp_servers integration)
   - This is the core functionality
   - Everything else depends on this

2. **Add Task 2** (rollback_configuration)
   - Required for User Journey 3
   - Completes the configuration lifecycle

3. **Add Task 3** (list_snapshots)
   - Nice-to-have for visibility
   - Quick win

4. **Validate with Task 4** (integration tests)
   - Ensures everything works together
   - Catches integration bugs

5. **Document with Task 5**
   - Update docs with working examples
   - Ensure users can actually use it

6. **Measure with Task 6**
   - Validate success criteria
   - Prove requirements are met

---

## 📝 NOTES FOR AI AGENT

### Critical Points
1. **Don't claim completion until integration tests pass**
2. **Actually test with real config files** (not just mocks)
3. **Measure performance** (don't just assume it's fast)
4. **Validate accuracy** (don't just claim 95%)

### Common Pitfalls to Avoid
1. Implementing components without integration
2. Returning "would be applied" instead of actually applying
3. Not testing end-to-end workflow
4. Not validating success criteria

### Definition of Done
- [ ] All 6 tasks complete
- [ ] All tests passing (including new integration tests)
- [ ] Documentation updated
- [ ] Success criteria validated and measured
- [ ] Can demonstrate working end-to-end workflow

---

**Current Status:** 30-40% functionally complete  
**Target Status:** 100% functionally complete  
**Estimated Time:** 2.75 hours  
**Priority:** P0 - Critical for production use
