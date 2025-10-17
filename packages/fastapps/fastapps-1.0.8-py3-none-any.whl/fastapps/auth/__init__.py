"""
FastApps Authentication Module

Provides built-in JWT verification, per-widget auth decorators,
and re-exports FastMCP auth components.
"""

from .verifier import JWTVerifier
from .decorators import auth_required, no_auth, optional_auth

# Re-export FastMCP auth components for convenience
try:
    from mcp.server.auth.provider import TokenVerifier, AccessToken
except ImportError:
    # Graceful fallback if fastmcp version doesn't have auth
    TokenVerifier = None
    AccessToken = None

__all__ = [
    "JWTVerifier",
    "TokenVerifier",
    "AccessToken",
    "auth_required",
    "no_auth",
    "optional_auth",
]

