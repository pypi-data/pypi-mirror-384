"""
Authentication and Authorization Module

Provides API authentication and input validation for OS Forge.
"""

import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials


# Security configuration
API_KEY = os.getenv("POLICY_GUARD_API_KEY", "dev-key-change-in-production")
security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Verify API key for authentication
    
    In production, this should use:
    - JWT tokens with proper expiration
    - OAuth2 flows
    - Database-backed API key management
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        str: Valid API key
        
    Raises:
        HTTPException: If API key is invalid
    """
    if credentials.credentials != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

