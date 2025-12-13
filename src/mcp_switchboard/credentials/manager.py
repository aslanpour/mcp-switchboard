"""Unified credential management."""
from __future__ import annotations
from typing import Dict, List
from .aws_sso import AWSSSOManager
from .oauth import OAuthManager
from .token_store import TokenStore


class CredentialManager:
    """Unified interface for credential management."""
    
    def __init__(self, oauth_automation: bool = False) -> None:
        self.aws_sso = AWSSSOManager()
        self.oauth = OAuthManager(automation_enabled=oauth_automation)
        self.token_store = TokenStore()
    
    async def prepare_credentials(self, server_configs: List[Dict]) -> Dict[str, bool]:
        """Prepare all required credentials for selected servers."""
        results = {}
        
        for config in server_configs:
            auth_type = config.get("authentication_type")
            server_name = config.get("name", "unknown")
            
            if auth_type == "aws_sso":
                profile = config.get("env", {}).get("AWS_PROFILE", "default")
                results[server_name] = await self.aws_sso.renew_if_needed(profile)
            
            elif auth_type == "api_token":
                token_key = self._get_token_key(config)
                token = self.token_store.get_token(token_key)
                results[server_name] = token is not None
            
            else:
                results[server_name] = True  # No auth needed
        
        return results
    
    def _get_token_key(self, config: Dict) -> str:
        """Generate token key from config."""
        server_name = config.get("name", "")
        env = config.get("env", {})
        
        if "atlassian" in server_name.lower() or "jira" in server_name.lower():
            email = env.get("ATLASSIAN_EMAIL", "default")
            return f"jira:{email}"
        elif "github" in server_name.lower():
            username = env.get("GITHUB_USERNAME", "default")
            return f"github:{username}"
        
        return server_name
