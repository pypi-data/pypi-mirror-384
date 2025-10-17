# Authentication

Server-wide OAuth 2.1 authentication for FastApps widgets.

## Overview

FastApps provides built-in support for OAuth 2.1 authentication, allowing you to protect your widgets and authenticate users. The framework handles all the complexity of the OAuth flow, token verification, and integration with ChatGPT's Apps SDK.

## Why Authentication?

Many widgets can operate in a read-only, anonymous mode, but anything that exposes customer-specific data or write actions should authenticate users:

- **User-specific data**: Display personalized content from your database
- **Write operations**: Create, update, or delete resources on behalf of users
- **Protected APIs**: Access services that require authentication
- **Multi-tenant apps**: Separate data between different users or organizations

## How It Works

FastApps uses OAuth 2.1 with PKCE (Proof Key for Code Exchange) to authenticate users:

1. **ChatGPT queries** your MCP server for protected resource metadata
2. **ChatGPT registers** itself with your authorization server
3. **User authenticates** when first invoking a protected tool
4. **ChatGPT obtains** an access token
5. **Your server verifies** the token on each request

All of this is handled automatically by FastApps and ChatGPT - you just configure it.

---

## Quick Start

### 1. Set Up Authorization Server

You need an OAuth 2.1 provider that supports:
- Dynamic client registration
- PKCE flow
- JWKS for token verification

**Recommended providers**: Auth0, Okta, Azure AD, AWS Cognito

### 2. Configure Your Server

Add authentication parameters to `WidgetMCPServer`:

```python
from fastapps import WidgetBuilder, WidgetMCPServer

# Build widgets
builder = WidgetBuilder(PROJECT_ROOT)
build_results = builder.build_all()
tools = auto_load_tools(build_results)

# Create server with authentication
server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://your-tenant.us.auth0.com",
    auth_resource_server_url="https://yourdomain.com/mcp",
    auth_required_scopes=["user"],
)

app = server.get_app()
```

That's it! Your widgets are now protected with OAuth.

---

## Built-in JWT Verification

FastApps includes a `JWTVerifier` that handles token validation automatically.

### Simple Example

```python
server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://tenant.auth0.com",
    auth_resource_server_url="https://example.com/mcp",
    auth_required_scopes=["user", "read:data"],
)
```

The built-in verifier automatically:
- Discovers JWKS URI from issuer's `.well-known/openid-configuration`
- Validates JWT signature using public keys
- Verifies issuer, audience, expiration
- Checks required scopes

### With Audience

If your OAuth provider requires an audience claim:

```python
server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://tenant.auth0.com",
    auth_resource_server_url="https://example.com/mcp",
    auth_audience="https://api.example.com",
    auth_required_scopes=["user"],
)
```

---

## Custom Token Verification

For advanced use cases, you can provide a custom `TokenVerifier`:

```python
from fastapps import WidgetMCPServer, TokenVerifier, AccessToken

class CustomVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # Custom validation logic
        # Example: Check database, rate limits, custom claims
        
        try:
            payload = my_custom_jwt_validation(token)
            
            # Custom authorization logic
            if not self.check_user_permissions(payload["sub"]):
                return None
            
            return AccessToken(
                token=token,
                client_id=payload["azp"],
                subject=payload["sub"],
                scopes=payload.get("permissions", []),
                claims=payload,
            )
        except Exception:
            return None
    
    def check_user_permissions(self, user_id: str) -> bool:
        # Your custom logic (database check, etc.)
        return True

server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://tenant.auth0.com",
    auth_resource_server_url="https://example.com/mcp",
    token_verifier=CustomVerifier(),
)
```

---

## Auth0 Setup

Auth0 is a popular OAuth provider with excellent support for dynamic client registration and ChatGPT integration.

### Step 1: Create an API

1. Go to Auth0 Dashboard → Applications → APIs
2. Click "Create API"
3. Enter:
   - **Name**: My FastApps API
   - **Identifier**: `https://api.example.com` (use your domain)
   - **Signing Algorithm**: RS256
4. Record the identifier (used as `auth_audience`)

### Step 2: Enable RBAC

1. In API Settings → RBAC Settings:
   - ✅ Enable RBAC
   - ✅ Add Permissions in the Access Token
2. Add permissions (scopes):
   - `user` - Basic user access
   - `read:data` - Read user data
   - `write:data` - Modify user data

### Step 3: Enable Dynamic Registration

1. Go to Settings → Advanced → OAuth
2. Toggle on "OIDC Dynamic Application Registration"
3. Ensure at least one connection is enabled (Google, Username-Password, etc.)

### Step 4: Configure FastApps

```python
server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://your-tenant.us.auth0.com",  # Your Auth0 domain
    auth_resource_server_url="https://yourdomain.com/mcp",  # Your server URL
    auth_audience="https://api.example.com",  # API identifier from step 1
    auth_required_scopes=["user"],
)
```

---

## Okta Setup

Okta also supports OAuth 2.1 with dynamic client registration.

### Step 1: Create Authorization Server

1. Go to Security → API → Authorization Servers
2. Record the Issuer URI (e.g., `https://dev-12345.okta.com/oauth2/default`)

### Step 2: Create Scopes

1. In your authorization server → Scopes
2. Add custom scopes:
   - `user` - User access
   - `read:data` - Read permissions

### Step 3: Enable Dynamic Client Registration

1. Go to Security → API → Trusted Origins
2. Add your server's origin

### Step 4: Configure FastApps

```python
server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://dev-12345.okta.com/oauth2/default",
    auth_resource_server_url="https://yourdomain.com/mcp",
    auth_required_scopes=["user"],
)
```

---

## Accessing User Information

When a widget is called with authentication, you can access user information through the `ClientContext`:

```python
from fastapps import BaseWidget, ClientContext

class ProtectedTool(BaseWidget):
    identifier = "protected"
    title = "Protected Widget"
    
    async def execute(self, input_data, context: ClientContext):
        # Access authenticated user info
        # Note: FastMCP passes token info through context
        
        return {
            "message": "Authenticated access granted",
            "user_location": context.user_location,
            "locale": context.locale,
        }
```

For full user claims from the JWT, you'll need to implement custom `TokenVerifier` and pass user info through your widget.

---

## Testing Authentication

### Local Testing

1. Start your server:
   ```bash
   python server/main.py
   ```

2. Expose with ngrok:
   ```bash
   ngrok http 8001
   ```

3. Add connector in ChatGPT:
   - Settings → Connectors → Add Connector
   - Use your ngrok URL: `https://xxxxx.ngrok-free.app/mcp`

4. Test a widget - ChatGPT will prompt for authentication

### Debugging

Enable debug logging to see auth flow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

server = WidgetMCPServer(...)
```

Check for:
- Token extraction from Authorization header
- JWKS discovery from issuer
- Token validation errors
- Scope mismatches

---

## Security Best Practices

### 1. Use HTTPS in Production

```python
auth_resource_server_url="https://yourdomain.com/mcp"  # Always HTTPS
```

### 2. Require Specific Scopes

```python
auth_required_scopes=["user", "read:data", "write:data"]
```

### 3. Short-lived Tokens

Configure your OAuth provider to issue short-lived access tokens (15 minutes - 1 hour).

### 4. Validate Audience

```python
auth_audience="https://api.example.com"  # Your API identifier
```

### 5. Monitor Failed Attempts

Implement custom `TokenVerifier` to log authentication failures:

```python
class MonitoredVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        result = await super().verify_token(token)
        if result is None:
            logging.warning(f"Token verification failed for token: {token[:20]}...")
        return result
```

---

## Common Issues

### Issue: "FastMCP auth support not available"

**Solution**: Upgrade fastmcp:
```bash
pip install --upgrade fastmcp
```

### Issue: "Failed to initialize JWKS"

**Solution**: Check that your `auth_issuer_url` is correct and accessible:
```bash
curl https://your-tenant.auth0.com/.well-known/openid-configuration
```

### Issue: "Token verification failed"

**Possible causes**:
- Token expired
- Wrong issuer URL
- Missing required scopes
- Audience mismatch

**Debug**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Issue: "401 Unauthorized" in ChatGPT

**Solution**: Check that:
1. Your authorization server is accessible from internet
2. Dynamic client registration is enabled
3. At least one login connection is enabled
4. `auth_resource_server_url` matches your public server URL

---

## Advanced: Per-Tool Authentication

Coming soon! You'll be able to mark individual widgets as requiring authentication:

```python
from fastapps import BaseWidget, auth_required

@auth_required(scopes=["write:data"])
class ProtectedWidget(BaseWidget):
    identifier = "protected"
    # ...
```

This feature is planned for the next release.

---

## Reference

### WidgetMCPServer Auth Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `auth_issuer_url` | `str` | Yes* | OAuth issuer URL (e.g., `https://tenant.auth0.com`) |
| `auth_resource_server_url` | `str` | Yes* | Your MCP server URL (e.g., `https://example.com/mcp`) |
| `auth_required_scopes` | `List[str]` | No | Required OAuth scopes (e.g., `["user", "read:data"]`) |
| `auth_audience` | `str` | No | JWT audience claim (required by some providers) |
| `token_verifier` | `TokenVerifier` | No | Custom token verifier (uses `JWTVerifier` if not provided) |

\* Both `auth_issuer_url` and `auth_resource_server_url` must be provided to enable auth.

### JWTVerifier Class

```python
from fastapps import JWTVerifier

verifier = JWTVerifier(
    issuer_url="https://tenant.auth0.com",
    audience="https://api.example.com",  # Optional
    required_scopes=["user", "read:data"]  # Optional
)
```

### TokenVerifier Interface

```python
from fastapps import TokenVerifier, AccessToken

class CustomVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        # Return AccessToken if valid, None if invalid
        pass
```

### AccessToken Class

```python
AccessToken(
    token=str,           # Original JWT token
    client_id=str,       # OAuth client ID
    subject=str,         # User identifier (sub claim)
    scopes=List[str],    # Granted scopes/permissions
    claims=Dict[str, Any]  # Full JWT payload
)
```

---

## Next Steps

- [Widget State](./04-STATE.md) - Manage user-specific state
- [API Integration](./06-API.md) - Call authenticated external APIs
- [Deployment](./09-DEPLOYMENT.md) - Deploy with authentication

---

**Questions?** Check our [GitHub Issues](https://github.com/fastapps-framework/fastapps/issues) or join our [Discord](https://discord.gg/fastapps).

