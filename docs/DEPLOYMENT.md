# Deployment Guide

## Building the Package

### Prerequisites

- Python 3.9+
- pip and setuptools
- twine (for PyPI upload)

### Build Distribution

```bash
# Install build tools
pip install build twine

# Build package
python -m build

# This creates:
# - dist/mcp_switchboard-0.1.0-py3-none-any.whl
# - dist/mcp-switchboard-0.1.0.tar.gz
```

### Verify Package

```bash
# Check package contents
tar -tzf dist/mcp-switchboard-0.1.0.tar.gz

# Verify package metadata
twine check dist/*
```

## Publishing to PyPI

### Test PyPI (Recommended First)

```bash
# Upload to Test PyPI
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ mcp-switchboard
```

### Production PyPI

```bash
# Upload to PyPI
twine upload dist/*

# Verify installation
pip install mcp-switchboard
```

## Installation Methods

### From PyPI (Production)

```bash
pip install mcp-switchboard
```

### From Source

```bash
git clone https://github.com/your-org/mcp-switchboard
cd mcp-switchboard
pip install -e .
```

### With Optional Dependencies

```bash
# Development tools
pip install mcp-switchboard[dev]

# Browser automation
pip install mcp-switchboard[automation]

# All extras
pip install mcp-switchboard[dev,automation]
```

## Docker Deployment

### Build Docker Image

```bash
# Create Dockerfile
cat > Dockerfile <<EOF
FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .

ENTRYPOINT ["mcp-switchboard"]
EOF

# Build image
docker build -t mcp-switchboard:0.1.0 .
```

### Run Container

```bash
docker run -it mcp-switchboard:0.1.0 --analyze "Deploy ECS to prod"
```

## Configuration

### System-wide Configuration

```bash
# Create config directory
mkdir -p ~/.mcp-switchboard

# Create config file
cat > ~/.mcp-switchboard/config.yaml <<EOF
auto_approve: false
oauth_automation: false
oauth_timeout_seconds: 300
state_database_path: ~/.mcp-switchboard/state.db
log_level: INFO
EOF
```

### Project-level Configuration

```bash
# Create project config
mkdir -p .mcp-switchboard
cp ~/.mcp-switchboard/config.yaml .mcp-switchboard/
```

## Verification

### Test Installation

```bash
# Check version
mcp-switchboard --version

# Test analysis
mcp-switchboard --analyze "Deploy ECS to prod Tokyo using DEVOPS-123"
```

### Run Tests

```bash
# Install dev dependencies
pip install mcp-switchboard[dev]

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src/mcp_switchboard --cov-report=html
```

### Run Benchmarks

```bash
python tests/benchmark.py
```

## Monitoring

### Logs

```bash
# View logs
tail -f ~/.mcp-switchboard/logs/app.log

# Parse JSON logs
cat ~/.mcp-switchboard/logs/app.log | jq '.'
```

### Metrics

```bash
# Check state database
sqlite3 ~/.mcp-switchboard/state.db "SELECT * FROM tasks ORDER BY created_at DESC LIMIT 10;"
```

## Troubleshooting

### Issue: Import errors

```bash
# Verify installation
pip show mcp-switchboard

# Reinstall
pip uninstall mcp-switchboard
pip install mcp-switchboard
```

### Issue: Permission errors

```bash
# Fix permissions
chmod -R 755 ~/.mcp-switchboard
```

### Issue: Database locked

```bash
# Close other processes
pkill -f mcp-switchboard

# Reset database
rm ~/.mcp-switchboard/state.db
```

## Upgrading

```bash
# Upgrade to latest version
pip install --upgrade mcp-switchboard

# Verify upgrade
mcp-switchboard --version
```

## Uninstallation

```bash
# Remove package
pip uninstall mcp-switchboard

# Remove configuration (optional)
rm -rf ~/.mcp-switchboard
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Test and Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e .[dev]
      - run: pytest tests/ --cov
      
  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

## Security

### Credential Storage

- Tokens stored in system keychain (macOS/Linux)
- Fallback to encrypted file storage
- Never commit credentials to git

### Best Practices

1. Use virtual environments
2. Pin dependency versions
3. Regular security audits
4. Keep dependencies updated
5. Use secrets management for CI/CD

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/mcp-switchboard/issues
- Documentation: https://github.com/your-org/mcp-switchboard/docs
