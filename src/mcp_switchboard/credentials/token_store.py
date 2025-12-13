"""Secure token storage using system keychain."""
from __future__ import annotations
from typing import Optional
import json
import os
from pathlib import Path


class TokenStore:
    """Store tokens securely."""
    
    SERVICE_NAME = "mcp-switchboard"
    
    def __init__(self, use_keychain: bool = True) -> None:
        self.use_keychain = use_keychain
        self._fallback_path = Path.home() / ".mcp-switchboard" / "tokens.json"
        
        if not use_keychain:
            self._fallback_path.parent.mkdir(parents=True, exist_ok=True)
    
    def store_token(self, key: str, token: str) -> None:
        """Store token securely."""
        if self.use_keychain:
            try:
                import keyring
                keyring.set_password(self.SERVICE_NAME, key, token)
                return
            except ImportError:
                pass
        
        # Fallback to file storage
        self._store_to_file(key, token)
    
    def get_token(self, key: str) -> Optional[str]:
        """Retrieve token."""
        if self.use_keychain:
            try:
                import keyring
                return keyring.get_password(self.SERVICE_NAME, key)
            except ImportError:
                pass
        
        # Fallback to file storage
        return self._get_from_file(key)
    
    def delete_token(self, key: str) -> None:
        """Delete token."""
        if self.use_keychain:
            try:
                import keyring
                keyring.delete_password(self.SERVICE_NAME, key)
                return
            except (ImportError, Exception):
                pass
        
        # Fallback to file storage
        self._delete_from_file(key)
    
    def _store_to_file(self, key: str, token: str) -> None:
        """Store token to file (fallback)."""
        tokens = {}
        if self._fallback_path.exists():
            with open(self._fallback_path) as f:
                tokens = json.load(f)
        
        tokens[key] = token
        
        with open(self._fallback_path, "w") as f:
            json.dump(tokens, f)
        
        # Set restrictive permissions
        os.chmod(self._fallback_path, 0o600)
    
    def _get_from_file(self, key: str) -> Optional[str]:
        """Get token from file (fallback)."""
        if not self._fallback_path.exists():
            return None
        
        with open(self._fallback_path) as f:
            tokens = json.load(f)
        
        return tokens.get(key)
    
    def _delete_from_file(self, key: str) -> None:
        """Delete token from file (fallback)."""
        if not self._fallback_path.exists():
            return
        
        with open(self._fallback_path) as f:
            tokens = json.load(f)
        
        tokens.pop(key, None)
        
        with open(self._fallback_path, "w") as f:
            json.dump(tokens, f)
