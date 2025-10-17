"""
Per-widget authentication decorators for FastApps.

Provides decorators to control authentication requirements per widget,
following the MCP securitySchemes specification.
"""

from typing import List, Optional, Type


def auth_required(scopes: Optional[List[str]] = None):
    """
    Require OAuth authentication for this widget.
    
    Sets securitySchemes metadata per MCP spec to require OAuth 2.0.
    The server enforces authentication regardless of client hints.
    
    Args:
        scopes: Optional list of required OAuth scopes (e.g., ["user", "write:data"])
    
    Example:
        @auth_required(scopes=["user", "write:data"])
        class ProtectedWidget(BaseWidget):
            identifier = "protected"
            
            async def execute(self, input_data, context, user):
                # User is guaranteed to be authenticated here
                return {"user_id": user.subject, "scopes": user.scopes}
    
    Example (no scopes):
        @auth_required
        class SimpleProtectedWidget(BaseWidget):
            identifier = "simple-protected"
            
            async def execute(self, input_data, context, user):
                return {"message": f"Hello, {user.subject}!"}
    """
    def decorator(cls: Type):
        cls._auth_required = True
        cls._auth_scopes = scopes or []
        # Per MCP spec: oauth2 type with optional scopes
        cls._security_schemes = [
            {"type": "oauth2", "scopes": scopes or []}
        ]
        return cls
    
    # Support both @auth_required and @auth_required()
    if callable(scopes):
        cls = scopes
        scopes = None
        return decorator(cls)
    
    return decorator


def no_auth(cls: Type):
    """
    Mark widget as explicitly public (no authentication required).
    
    Use this to opt-out of server-wide authentication.
    Sets securitySchemes to [{"type": "noauth"}] per MCP spec.
    
    Args:
        cls: The widget class to decorate
    
    Example:
        @no_auth
        class PublicWidget(BaseWidget):
            identifier = "public"
            
            async def execute(self, input_data, context, user):
                # Accessible to everyone, user may be None
                return {"message": "Public content"}
    """
    cls._auth_required = False
    cls._security_schemes = [{"type": "noauth"}]
    return cls


def optional_auth(scopes: Optional[List[str]] = None):
    """
    Support both authenticated and anonymous access.
    
    Per MCP spec, declaring both "noauth" and "oauth2" types means
    anonymous access works, but authenticating unlocks more features.
    
    Widget should check user.is_authenticated to provide different
    functionality based on authentication status.
    
    Args:
        scopes: Optional list of scopes to request if user authenticates
    
    Example:
        @optional_auth(scopes=["user"])
        class FlexibleWidget(BaseWidget):
            identifier = "flexible"
            
            async def execute(self, input_data, context, user):
                if user.is_authenticated:
                    # Premium features for authenticated users
                    return {
                        "tier": "premium",
                        "user": user.subject,
                        "features": ["advanced", "export", "share"]
                    }
                
                # Basic features for everyone
                return {
                    "tier": "basic",
                    "features": ["view"]
                }
    """
    def decorator(cls: Type):
        cls._auth_required = False
        cls._auth_scopes = scopes or []
        # Per MCP spec: both types means optional authentication
        cls._security_schemes = [
            {"type": "noauth"},
            {"type": "oauth2", "scopes": scopes or []}
        ]
        return cls
    
    # Support both @optional_auth and @optional_auth()
    if callable(scopes):
        cls = scopes
        scopes = None
        return decorator(cls)
    
    return decorator

