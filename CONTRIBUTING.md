# Contributing to mcp-switchboard

Thank you for your interest in contributing! This document provides guidelines for contributing to mcp-switchboard.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.9+
- Git
- Virtual environment tool (venv, virtualenv, or conda)

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/your-org/mcp-switchboard
cd mcp-switchboard

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e .[dev]

# Run tests to verify setup
pytest tests/ -v
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write minimal, focused code
- Follow existing code patterns
- Add type hints to all functions
- Write docstrings for public APIs

### 3. Add Tests

```bash
# Create test file in tests/
# Follow naming: test_<module>.py

# Run tests
pytest tests/test_your_module.py -v

# Check coverage
pytest tests/ --cov=src/mcp_switchboard --cov-report=html
```

### 4. Format Code

```bash
# Format with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature

- Detailed description
- What changed
- Why it changed"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### 6. Push and Create PR

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub.

## Code Style

### Python Style

- Follow PEP 8
- Use Black formatter (line length: 100)
- Use type hints everywhere
- Write docstrings for public functions

**Example:**

```python
from typing import Optional

def analyze_task(
    task_description: str,
    project_path: Optional[str] = None
) -> TaskAnalysis:
    """Analyze task description to extract structured information.
    
    Args:
        task_description: Natural language task description
        project_path: Optional path to project directory
        
    Returns:
        TaskAnalysis with extracted information
    """
    # Implementation
    pass
```

### Testing Style

- One test file per module
- Descriptive test names
- Arrange-Act-Assert pattern
- Mock external dependencies

**Example:**

```python
def test_analyze_complete_task():
    """Test task analysis with all fields present."""
    # Arrange
    analyzer = TaskAnalyzer()
    task = "Deploy ECS to prod Tokyo using DEVOPS-123"
    
    # Act
    result = analyzer.analyze(task)
    
    # Assert
    assert result.aws_account == "prod"
    assert result.aws_region == "ap-northeast-1"
    assert result.jira_ticket == "DEVOPS-123"
```

## Project Structure

```
mcp-switchboard/
├── src/mcp_switchboard/    # Source code
│   ├── analyzer/           # Task analysis
│   ├── selector/           # Server selection
│   ├── credentials/        # Credential management
│   ├── config/            # Configuration
│   └── ...
├── tests/                 # Test suite
├── docs/                  # Documentation
├── pyproject.toml         # Project config
└── README.md
```

## Adding New Features

### 1. Task Analyzer Enhancement

To add new parsing capabilities:

```python
# src/mcp_switchboard/analyzer/parser.py

def parse(self, task_description: str) -> ParsedTask:
    # Add new extraction logic
    new_field = self._extract_new_field(task_description)
    
    return ParsedTask(
        # ... existing fields
        new_field=new_field
    )
```

### 2. Server Registry Addition

To add new MCP server:

```yaml
# src/mcp_switchboard/config/registry.yaml

servers:
  new-mcp-server:
    capabilities: ["capability1", "capability2"]
    authentication_type: "api_token"
    env:
      API_KEY: "${NEW_SERVER_API_KEY}"
```

### 3. Credential Provider

To add new authentication type:

```python
# src/mcp_switchboard/credentials/new_provider.py

class NewAuthProvider:
    async def check_credentials(self) -> CredentialStatus:
        # Implementation
        pass
    
    async def renew_credentials(self) -> bool:
        # Implementation
        pass
```

## Testing Guidelines

### Unit Tests

Test individual functions in isolation:

```python
def test_parse_aws_account():
    parser = TaskParser()
    result = parser.parse("Deploy to prod")
    assert result.aws_account == "prod"
```

### Integration Tests

Test component interactions:

```python
def test_full_analysis_workflow():
    analyzer = TaskAnalyzer()
    selector = ServerSelector(ServerRegistry())
    
    analysis = analyzer.analyze("Deploy ECS to prod")
    selection = selector.select(analysis)
    
    assert len(selection.selected_servers) > 0
```

### Performance Tests

Benchmark critical paths:

```python
def test_analysis_performance():
    analyzer = TaskAnalyzer()
    
    start = time.perf_counter()
    analyzer.analyze("Deploy ECS to prod")
    duration = time.perf_counter() - start
    
    assert duration < 0.1  # 100ms
```

## Documentation

### Code Documentation

- Add docstrings to all public functions
- Include type hints
- Provide usage examples

### User Documentation

Update relevant docs when adding features:
- `README.md` - Overview and quick start
- `docs/API.md` - API reference
- `docs/USER-GUIDE.md` - Usage examples

## Pull Request Process

1. **Update tests** - Add tests for new functionality
2. **Update docs** - Document new features
3. **Run full test suite** - Ensure all tests pass
4. **Update CHANGELOG.md** - Add entry under [Unreleased]
5. **Create PR** - Provide clear description
6. **Address feedback** - Respond to review comments

### PR Checklist

- [ ] Tests added/updated
- [ ] All tests passing
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Code formatted (black)
- [ ] No linting errors (ruff)
- [ ] Type hints added (mypy)

## Release Process

Maintainers only:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md` (move [Unreleased] to version)
3. Create git tag: `git tag -a v0.x.0 -m "Release v0.x.0"`
4. Build package: `python -m build`
5. Upload to PyPI: `twine upload dist/*`
6. Create GitHub release

## Questions?

- Open an issue for bugs or feature requests
- Start a discussion for questions
- Check existing issues before creating new ones

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
