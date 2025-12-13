# mcp-switchboard

Intelligent MCP server orchestrator that automates configuration, orchestration, and lifecycle management of other MCP servers for AI agents.

## Status

🚧 **Under Development** - Phase 1: Core Foundation

## Quick Start

```bash
# Install dependencies
poetry install

# Run server
poetry run mcp-switchboard
```

## Development

```bash
# Run tests
poetry run pytest

# Format code
poetry run black src/ tests/

# Lint
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/
```

## Documentation

See `../mcp-switchboard-spec/` for complete specification and implementation guide.
