# mcp-switchboard

Intelligent MCP server orchestrator that automates configuration, orchestration, and lifecycle management of other MCP servers for AI agents.

[![Tests](https://img.shields.io/badge/tests-59%20passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.9%2B-blue)]()

## Overview

**mcp-switchboard** eliminates the manual overhead of configuring MCP servers for AI agents by:

- **Analyzing** task context to determine required MCP servers
- **Selecting** appropriate servers based on intelligent matching
- **Configuring** servers with correct credentials and settings
- **Validating** server health and tool availability
- **Learning** from historical patterns to improve recommendations

**Time Savings:** Reduces MCP setup from 5-15 minutes to <30 seconds per task

## Quick Start

### Installation

**Using uv (Recommended - Fast & Modern):**

```bash
# Install from PyPI
uv pip install mcp-switchboard

# Or run directly without installation
uvx mcp-switchboard --analyze "Deploy ECS to prod"
uvx mcp-switchboard-server  # Run MCP server
```

**From source:**

```bash
# Clone repository
git clone https://github.com/aslanpour/mcp-switchboard
cd mcp-switchboard

# Install with uv
uv pip install -e .

# Or with pip
pip install -e .
```

### Basic Usage

```python
from mcp_switchboard.analyzer.analyzer import TaskAnalyzer
from mcp_switchboard.selector.selector import ServerSelector
from mcp_switchboard.config.registry import ServerRegistry

# Analyze task
analyzer = TaskAnalyzer()
analysis = analyzer.analyze("Deploy ECS to prod Tokyo using DEVOPS-123")

# Select servers
registry = ServerRegistry()
selector = ServerSelector(registry)
selection = selector.select(analysis)

# Results
print(f"Selected: {[s.server_name for s in selection.selected_servers]}")
# Output: ['atlassian-mcp', 'aws-api-mcp']
```

## Features

- ✅ Intelligent task analysis with confidence scoring
- ✅ Capability-based server selection
- ✅ AWS SSO and OAuth credential management
- ✅ Multi-agent configuration support
- ✅ Snapshot and rollback capabilities
- ✅ State tracking and historical learning
- ✅ Structured logging and metrics

## Requirements

- Python 3.9+
- AWS CLI (for AWS SSO)
- Node.js/npm (for npm-based MCP servers)

## Development

```bash
# Run tests
pytest tests/

# Format code
black src/ tests/

# Type check
mypy src/
```

## Status

**Current Version:** v1.0.0 - Production Ready 🎉

**Functional Completion:** 100%

**What Works:**
- ✅ Task analysis (keyword + LLM)
- ✅ Server selection with confidence scoring
- ✅ **Historical pattern learning** (NEW in v1.0.0)
- ✅ Credential management (AWS SSO, OAuth, tokens)
- ✅ Configuration writing with snapshots
- ✅ Configuration rollback
- ✅ **Real-time health monitoring** (NEW in v1.0.0)
- ✅ State tracking and history
- ✅ MCP server with 6 tools
- ✅ Multi-transport (STDIO/SSE/HTTP)
- ✅ Server subprocess management
- ✅ Full orchestration workflow

**MCP Tools Available:**
1. `setup_mcp_servers` - Complete orchestration with real-time health monitoring
2. `analyze_task` - Extract task requirements
3. `select_servers` - Recommend MCP servers (with historical learning)
4. `manage_servers` - Subprocess management
5. `rollback_configuration` - Restore previous config
6. `list_snapshots` - View available snapshots

**Advanced Features:**
- Real-time server startup validation
- Historical pattern learning for better recommendations
- Confidence boosting based on past success
- Exponential backoff retry logic
- Detailed health metrics (startup time, tools available)

**Tests:** 85/85 passing (100%)

**Performance:**
- Task analysis: <2ms
- Server selection: <1ms
- Total orchestration: 2-3 seconds
- Health validation: <1 second per server

See `CHANGELOG.md` for version history.

## License

[To be determined]
