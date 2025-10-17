"""
Authentication module for MCP OpenProject HTTP Server
Handles client authentication using encryption key
"""

import os
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, Security, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Security scheme for API key authentication
security = HTTPBearer(auto_error=False)

class MCPAuthenticator:
    """Handles MCP client authentication using encryption key"""
    
    def __init__(self):
        self.encryption_key = os.getenv("ENCRYPTION_KEY")
        if not self.encryption_key:
            raise ValueError("ENCRYPTION_KEY environment variable is required")
    
    def verify_token(self, token: str) -> bool:
        """Verify MCP client token using HMAC"""
        try:
            # Simple HMAC-based token verification
            # In production, you might want to use JWT or more sophisticated methods
            expected = hmac.new(
                self.encryption_key.encode(),
                b"mcp-client-auth",
                hashlib.sha256
            ).hexdigest()
            
            # For now, accept the encryption key directly as token
            # In production, implement proper token generation/validation
            return hmac.compare_digest(token, self.encryption_key)
        except Exception:
            return False
    
    def generate_client_config(self) -> dict:
        """Generate client configuration for MCP clients"""
        return {
            "auth_type": "bearer_token",
            "auth_token": self.encryption_key,
            "auth_header": "Authorization",
            "auth_scheme": "Bearer"
        }

# Global authenticator instance
_authenticator = None

def get_authenticator() -> MCPAuthenticator:
    """Get or create authenticator instance"""
    global _authenticator
    if _authenticator is None:
        _authenticator = MCPAuthenticator()
    return _authenticator

async def verify_mcp_client(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """FastAPI dependency to verify MCP client authentication"""
    authenticator = get_authenticator()
    
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authenticator.verify_token(credentials.credentials):
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials

def get_client_auth_info() -> dict:
    """Get authentication information for client configuration"""
    return get_authenticator().generate_client_config()
