"""OAuth flow management."""
from __future__ import annotations
import webbrowser
import re
from typing import Optional


class OAuthManager:
    """Manage OAuth authentication flows."""
    
    def __init__(self, automation_enabled: bool = False) -> None:
        self.automation_enabled = automation_enabled
    
    def detect_oauth_url(self, command_output: str) -> Optional[str]:
        """Extract OAuth URL from command output."""
        patterns = [
            r'https://[^\s]+/oauth/authorize[^\s]*',
            r'https://[^\s]+/login[^\s]*',
            r'https://[^\s]+/auth[^\s]*',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command_output)
            if match:
                return match.group(0)
        
        return None
    
    def open_browser(self, url: str) -> bool:
        """Open OAuth URL in default browser."""
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False
