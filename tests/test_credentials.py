"""Tests for credential management."""
import pytest
import tempfile
from pathlib import Path
from mcp_switchboard.credentials.aws_sso import AWSCredentialStatus, AWSSSOManager
from mcp_switchboard.credentials.oauth import OAuthManager
from mcp_switchboard.credentials.token_store import TokenStore
from mcp_switchboard.credentials.manager import CredentialManager


def test_credential_status():
    """Test credential status."""
    status = AWSCredentialStatus(valid=True)
    assert status.valid is True
    assert status.needs_renewal is False
    
    status = AWSCredentialStatus(valid=False)
    assert status.needs_renewal is True


def test_oauth_detect_url():
    """Test OAuth URL detection."""
    manager = OAuthManager()
    
    output = "Please visit https://example.com/oauth/authorize?code=123"
    url = manager.detect_oauth_url(output)
    assert url == "https://example.com/oauth/authorize?code=123"
    
    output = "No URL here"
    url = manager.detect_oauth_url(output)
    assert url is None


def test_token_store_file_fallback():
    """Test token store with file fallback."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = TokenStore(use_keychain=False)
        store._fallback_path = Path(tmpdir) / "tokens.json"
        
        # Store token
        store.store_token("test_key", "test_token")
        
        # Retrieve token
        token = store.get_token("test_key")
        assert token == "test_token"
        
        # Delete token
        store.delete_token("test_key")
        token = store.get_token("test_key")
        assert token is None


def test_token_store_nonexistent():
    """Test getting nonexistent token."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = TokenStore(use_keychain=False)
        store._fallback_path = Path(tmpdir) / "tokens.json"
        
        token = store.get_token("nonexistent")
        assert token is None


def test_credential_manager_no_auth():
    """Test credential manager with no auth required."""
    import asyncio
    
    manager = CredentialManager()
    
    configs = [
        {"name": "test-server", "authentication_type": "none"}
    ]
    
    results = asyncio.run(manager.prepare_credentials(configs))
    assert results["test-server"] is True


def test_credential_manager_token_key():
    """Test token key generation."""
    manager = CredentialManager()
    
    jira_config = {
        "name": "atlassian-mcp",
        "env": {"ATLASSIAN_EMAIL": "user@example.com"}
    }
    key = manager._get_token_key(jira_config)
    assert key == "jira:user@example.com"
    
    github_config = {
        "name": "github-mcp",
        "env": {"GITHUB_USERNAME": "testuser"}
    }
    key = manager._get_token_key(github_config)
    assert key == "github:testuser"
