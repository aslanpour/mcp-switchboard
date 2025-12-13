"""AWS SSO credential management."""
from __future__ import annotations
import asyncio
from typing import Optional
from datetime import datetime, timedelta


class AWSCredentialStatus:
    """Status of AWS credentials."""
    
    def __init__(self, valid: bool, expires_at: Optional[datetime] = None) -> None:
        self.valid = valid
        self.expires_at = expires_at
    
    @property
    def needs_renewal(self) -> bool:
        """Check if credentials need renewal."""
        if not self.valid:
            return True
        if self.expires_at and self.expires_at < datetime.now() + timedelta(minutes=5):
            return True
        return False


class AWSSSOManager:
    """Manage AWS SSO credentials."""
    
    async def check_credentials(self, profile: str) -> AWSCredentialStatus:
        """Check if AWS SSO credentials are valid."""
        try:
            process = await asyncio.create_subprocess_exec(
                "aws", "sts", "get-caller-identity",
                "--profile", profile,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return AWSCredentialStatus(valid=True)
            else:
                return AWSCredentialStatus(valid=False)
        except Exception:
            return AWSCredentialStatus(valid=False)
    
    async def renew_credentials(self, profile: str, timeout: int = 300) -> bool:
        """Renew AWS SSO credentials via browser login."""
        try:
            process = await asyncio.create_subprocess_exec(
                "aws", "sso", "login",
                "--profile", profile,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                await asyncio.wait_for(process.wait(), timeout=timeout)
            except asyncio.TimeoutError:
                process.kill()
                return False
            
            # Verify credentials after renewal
            status = await self.check_credentials(profile)
            return status.valid
        except Exception:
            return False
    
    async def renew_if_needed(self, profile: str) -> bool:
        """Check and renew credentials if needed."""
        status = await self.check_credentials(profile)
        
        if status.needs_renewal:
            return await self.renew_credentials(profile)
        
        return True
