"""
Built-in JWT Token Verifier for FastApps

Provides automatic JWT validation with JWKS discovery for Auth0, Okta, Azure AD,
and other OAuth 2.1 providers.
"""

from typing import Optional, List
import httpx

try:
    from mcp.server.auth.provider import TokenVerifier, AccessToken
    import jwt
    from jwt import PyJWKClient
    MCP_AUTH_AVAILABLE = True
except ImportError:
    MCP_AUTH_AVAILABLE = False
    TokenVerifier = object
    AccessToken = None


class JWTVerifier(TokenVerifier):
    """
    Built-in JWT verifier for FastApps.
    
    Handles standard JWT validation with JWKS auto-discovery.
    Supports Auth0, Okta, Azure AD, and custom OAuth 2.1 providers.
    
    Example:
        verifier = JWTVerifier(
            issuer_url="https://your-tenant.us.auth0.com",
            audience="https://api.example.com",
            required_scopes=["user", "read:data"]
        )
    """
    
    def __init__(
        self,
        issuer_url: str,
        audience: Optional[str] = None,
        required_scopes: Optional[List[str]] = None
    ):
        """
        Initialize JWT verifier with automatic JWKS discovery.
        
        Args:
            issuer_url: OAuth issuer URL (e.g., https://tenant.auth0.com)
            audience: Expected audience claim in JWT (optional)
            required_scopes: List of required scopes/permissions (optional)
        
        Raises:
            RuntimeError: If JWKS discovery fails
            ImportError: If required dependencies are not installed
        """
        if not MCP_AUTH_AVAILABLE:
            raise ImportError(
                "Authentication dependencies not available. "
                "Install with: pip install 'PyJWT>=2.8.0' 'cryptography>=41.0.0'"
            )
        
        self.issuer_url = issuer_url.rstrip('/')
        self.audience = audience
        self.required_scopes = required_scopes or []
        
        # Auto-discover JWKS URL from issuer
        self.jwks_client = None
        self._initialize_jwks()
    
    def _initialize_jwks(self):
        """
        Fetch JWKS URI from OpenID configuration.
        
        Queries the issuer's .well-known/openid-configuration endpoint
        to discover the JWKS URI for token verification.
        """
        try:
            discovery_url = f"{self.issuer_url}/.well-known/openid-configuration"
            response = httpx.get(discovery_url, timeout=10)
            response.raise_for_status()
            config = response.json()
            
            jwks_uri = config.get('jwks_uri')
            if not jwks_uri:
                raise ValueError("No jwks_uri found in OpenID configuration")
            
            self.jwks_client = PyJWKClient(jwks_uri)
            
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize JWKS from {self.issuer_url}: {e}"
            )
    
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """
        Verify JWT token and return AccessToken if valid.
        
        Args:
            token: JWT token string from Authorization header
        
        Returns:
            AccessToken object if valid, None if invalid
        """
        try:
            # Get signing key from JWKS
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            
            # Decode and verify JWT
            decode_options = {
                "verify_signature": True,
                "verify_exp": True,
                "verify_iat": True,
                "verify_aud": self.audience is not None,
            }
            
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                issuer=self.issuer_url,
                audience=self.audience,
                options=decode_options
            )
            
            # Extract scopes from token
            # Auth0 uses "permissions", some providers use "scope" (space-separated)
            token_scopes = []
            if "permissions" in payload:
                token_scopes = payload["permissions"]
            elif "scope" in payload:
                token_scopes = payload["scope"].split() if isinstance(payload["scope"], str) else payload["scope"]
            
            # Verify required scopes
            if self.required_scopes:
                missing_scopes = set(self.required_scopes) - set(token_scopes)
                if missing_scopes:
                    # Token is valid but lacks required scopes
                    return None
            
            # Build AccessToken
            return AccessToken(
                token=token,
                client_id=payload.get("azp") or payload.get("client_id") or payload.get("aud"),
                subject=payload["sub"],
                scopes=token_scopes,
                claims=payload,
            )
            
        except jwt.ExpiredSignatureError:
            # Token expired
            return None
        except jwt.InvalidTokenError:
            # Token invalid (bad signature, malformed, etc.)
            return None
        except Exception:
            # Any other error (network, parsing, etc.)
            return None

