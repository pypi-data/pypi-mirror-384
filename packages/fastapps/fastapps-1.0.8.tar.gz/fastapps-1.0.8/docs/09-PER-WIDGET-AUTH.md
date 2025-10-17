# Per-Widget Authentication

Control authentication requirements for individual widgets using decorators.

## Overview

FastApps supports per-widget authentication through decorators that comply with the MCP `securitySchemes` specification. This allows you to:

- Require authentication for specific widgets
- Opt-out of server-wide authentication for public widgets
- Support both authenticated and anonymous access (optional auth)
- Access authenticated user information in your widget

## Quick Start

### Protected Widget

```python
from fastapps import BaseWidget, auth_required, UserContext

@auth_required(scopes=["user", "write:data"])
class ProtectedWidget(BaseWidget):
    identifier = "protected"
    title = "Protected Widget"
    input_schema = ProtectedInput
    
    async def execute(self, input_data, context, user: UserContext):
        # User is guaranteed to be authenticated here
        return {
            "user_id": user.subject,
            "name": user.claims.get('name', 'User'),
            "scopes": user.scopes
        }
```

### Public Widget (Opt-out)

```python
from fastapps import BaseWidget, no_auth

@no_auth
class PublicWidget(BaseWidget):
    identifier = "public"
    title = "Public Widget"
    
    async def execute(self, input_data, context, user):
        # Always accessible, user may not be authenticated
        return {"message": "Public content for everyone"}
```

### Optional Authentication

```python
from fastapps import BaseWidget, optional_auth, UserContext

@optional_auth(scopes=["user"])
class FlexibleWidget(BaseWidget):
    identifier = "flexible"
    title = "Flexible Widget"
    
    async def execute(self, input_data, context, user: UserContext):
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
```

---

## Decorators

### @auth_required

Require OAuth authentication for this widget.

**Syntax:**
```python
@auth_required
@auth_required()
@auth_required(scopes=["user"])
@auth_required(scopes=["user", "write:data"])
```

**Parameters:**
- `scopes` (optional): List of required OAuth scopes

**Behavior:**
- Sets `securitySchemes: [{"type": "oauth2", "scopes": [...]}]`
- Server enforces authentication before calling widget
- Missing scopes result in error

**Example:**
```python
@auth_required(scopes=["admin"])
class AdminWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # Only users with "admin" scope can access
        return {"admin_data": "..."}
```

### @no_auth

Mark widget as explicitly public (no authentication required).

**Syntax:**
```python
@no_auth
class MyWidget(BaseWidget):
    ...
```

**Behavior:**
- Sets `securitySchemes: [{"type": "noauth"}]`
- Widget accessible to everyone
- Opt-out of server-wide authentication
- `user` parameter may be None

**Example:**
```python
@no_auth
class SearchWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # Public search - no auth needed
        return {"results": search(input_data.query)}
```

### @optional_auth

Support both authenticated and anonymous access.

**Syntax:**
```python
@optional_auth
@optional_auth()
@optional_auth(scopes=["user"])
```

**Parameters:**
- `scopes` (optional): Scopes to request if user authenticates

**Behavior:**
- Sets `securitySchemes: [{"type": "noauth"}, {"type": "oauth2", "scopes": [...]}]`
- Per MCP spec: both types means optional authentication
- Widget should check `user.is_authenticated` to provide different features

**Example:**
```python
@optional_auth(scopes=["user"])
class ContentWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        content = get_content(input_data.id)
        
        if user.is_authenticated:
            # Show full content + personalization
            return {
                "content": content,
                "personalized": True,
                "recommendations": get_recommendations(user.subject)
            }
        
        # Show preview only
        return {
            "content": content[:100] + "...",
            "personalized": False
        }
```

---

## UserContext

Access authenticated user information through the `UserContext` object passed to `execute()`.

### Properties

#### `is_authenticated: bool`
Whether user is authenticated.

```python
if user.is_authenticated:
    return {"message": f"Hello, {user.subject}!"}
```

#### `subject: Optional[str]`
User identifier from JWT `sub` claim.

```python
user_id = user.subject  # e.g., "auth0|123456"
```

#### `client_id: Optional[str]`
OAuth client ID.

```python
client = user.client_id
```

#### `scopes: List[str]`
Granted OAuth scopes.

```python
user_scopes = user.scopes  # e.g., ["user", "read:data"]
```

#### `claims: Dict[str, Any]`
Full JWT claims dictionary.

```python
email = user.claims.get('email')
name = user.claims.get('name')
custom_data = user.claims.get('custom_field')
```

### Methods

#### `has_scope(scope: str) -> bool`
Check if user has specific scope.

```python
if user.has_scope("admin"):
    return {"admin_panel": True}
elif user.has_scope("user"):
    return {"user_panel": True}
else:
    return {"error": "Insufficient permissions"}
```

---

## Authentication Inheritance

Per MCP spec: "Missing field: inherit server default policy"

### Inheritance Rules

| Server Auth | Widget Decorator | Result |
|-------------|------------------|--------|
| **Enabled** | None | Required (inherits server) |
| **Enabled** | @auth_required | Required (widget-specific scopes) |
| **Enabled** | @no_auth | Public (opt-out) |
| **Enabled** | @optional_auth | Optional |
| **Disabled** | None | Public |
| **Disabled** | @auth_required | Required |
| **Disabled** | @no_auth | Public |
| **Disabled** | @optional_auth | Optional |

### Examples

**Scenario 1: Server has auth, widget has none**
```python
# server/main.py
server = WidgetMCPServer(
    name="my-widgets",
    widgets=tools,
    auth_issuer_url="https://tenant.auth0.com",
    auth_resource_server_url="https://example.com/mcp",
    auth_required_scopes=["user"],
)

# server/tools/my_widget_tool.py
class MyWidgetTool(BaseWidget):
    # No decorator - inherits server auth
    # Requires: ["user"] scope
    ...
```

**Scenario 2: Server has auth, widget opts out**
```python
# server/main.py (same as above - server requires auth)

# server/tools/public_widget_tool.py
@no_auth
class PublicWidgetTool(BaseWidget):
    # Explicitly public despite server auth
    ...
```

---

## Scope Enforcement

### Widget-Specific Scopes

```python
@auth_required(scopes=["admin", "write:sensitive"])
class SensitiveWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # User must have BOTH "admin" AND "write:sensitive"
        return {"sensitive_data": "..."}
```

### Checking Scopes in Code

```python
@auth_required
class FlexibleAdminWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        if user.has_scope("super_admin"):
            return {"level": "full_access"}
        elif user.has_scope("admin"):
            return {"level": "limited_access"}
        else:
            return {"error": "Insufficient permissions"}
```

### Multiple Scope Strategies

```python
@optional_auth(scopes=["user"])
class MultiTierWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        if not user.is_authenticated:
            return {"tier": "free", "features": ["basic"]}
        
        if user.has_scope("premium"):
            return {"tier": "premium", "features": ["basic", "advanced", "export"]}
        
        if user.has_scope("user"):
            return {"tier": "standard", "features": ["basic", "advanced"]}
        
        return {"tier": "free", "features": ["basic"]}
```

---

## Best Practices

### 1. Use Specific Scopes

```python
# Good: Specific scopes for different operations
@auth_required(scopes=["user", "write:documents"])
class CreateDocumentWidget(BaseWidget):
    ...

# Less ideal: Generic scope for everything
@auth_required(scopes=["user"])
class CreateDocumentWidget(BaseWidget):
    ...
```

### 2. Check Authentication Status in Optional Auth

```python
@optional_auth(scopes=["user"])
class SmartWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # Always check is_authenticated for optional auth
        if user.is_authenticated:
            return self._authenticated_version(user)
        return self._public_version()
```

### 3. Provide Helpful Error Messages

```python
@auth_required(scopes=["admin"])
class AdminWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        if not user.has_scope("admin"):
            return {
                "error": "Admin access required",
                "message": "Contact your administrator for access"
            }
        # ...
```

### 4. Use Type Hints

```python
from fastapps import UserContext

async def execute(self, input_data, context, user: UserContext):
    # IDE will autocomplete user.subject, user.scopes, etc.
    ...
```

### 5. Opt-out When Appropriate

```python
# Public widgets should explicitly opt-out
@no_auth
class PublicSearchWidget(BaseWidget):
    # Makes intent clear
    ...
```

---

## Security Considerations

### 1. Server-Side Enforcement

Per MCP spec: "Servers must enforce regardless of client hints"

FastApps enforces authentication **server-side**. The `securitySchemes` metadata helps clients guide users, but the server always validates tokens and scopes.

### 2. Don't Trust Client Data

```python
@auth_required
class UserDataWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # Good: Use authenticated user.subject
        user_data = get_user_data(user.subject)
        
        # Bad: Trust user-supplied ID (input_data.user_id)
        # user_data = get_user_data(input_data.user_id)
```

### 3. Validate Scopes

```python
@auth_required(scopes=["admin"])
class DeleteWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # Double-check critical operations
        if not user.has_scope("admin"):
            return {"error": "Unauthorized"}
        
        # Proceed with deletion
        ...
```

### 4. Log Authentication Events

```python
@auth_required
class SensitiveWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        # Log access for audit trail
        log_access(
            user_id=user.subject,
            action="accessed_sensitive_data",
            timestamp=datetime.utcnow()
        )
        ...
```

---

## Examples

### Admin Dashboard

```python
from fastapps import BaseWidget, auth_required, UserContext

@auth_required(scopes=["admin"])
class AdminDashboardWidget(BaseWidget):
    identifier = "admin-dashboard"
    title = "Admin Dashboard"
    input_schema = AdminDashboardInput
    
    async def execute(self, input_data, context, user: UserContext):
        # Verify admin scope (already enforced, but double-check)
        if not user.has_scope("admin"):
            return {"error": "Admin access required"}
        
        # Fetch admin data
        stats = await get_admin_stats()
        users = await get_user_list()
        
        return {
            "admin": user.subject,
            "stats": stats,
            "users": users,
            "permissions": user.scopes
        }
```

### Personalized Content

```python
@optional_auth(scopes=["user"])
class PersonalizedContentWidget(BaseWidget):
    identifier = "personalized-content"
    title = "Personalized Content"
    
    async def execute(self, input_data, context, user: UserContext):
        content = await fetch_content(input_data.content_id)
        
        if user.is_authenticated:
            # Add personalization
            user_preferences = await get_preferences(user.subject)
            recommendations = await get_recommendations(user.subject)
            
            return {
                "content": content,
                "personalized": True,
                "preferences": user_preferences,
                "recommendations": recommendations
            }
        
        # Public version
        return {
            "content": content,
            "personalized": False,
            "message": "Sign in for personalized experience"
        }
```

### Role-Based Access

```python
@auth_required(scopes=["user"])
class RoleBasedWidget(BaseWidget):
    identifier = "role-based"
    title = "Role-Based Widget"
    
    async def execute(self, input_data, context, user: UserContext):
        # Check role from claims
        role = user.claims.get('role', 'user')
        
        if role == 'admin':
            return await self._admin_view(user)
        elif role == 'manager':
            return await self._manager_view(user)
        else:
            return await self._user_view(user)
    
    async def _admin_view(self, user):
        return {"view": "admin", "data": "all_data"}
    
    async def _manager_view(self, user):
        return {"view": "manager", "data": "team_data"}
    
    async def _user_view(self, user):
        return {"view": "user", "data": "personal_data"}
```

---

## Troubleshooting

### Issue: User is always None

**Possible causes:**
1. Server auth not configured
2. User not authenticated in ChatGPT
3. Token verification failing

**Solution:**
```python
# Check if widget requires auth
@auth_required
class MyWidget(BaseWidget):
    async def execute(self, input_data, context, user):
        if not user.is_authenticated:
            # This shouldn't happen with @auth_required
            return {"error": "Authentication failed"}
        ...
```

### Issue: "Missing required scopes" error

**Cause:** User doesn't have required scopes

**Solution:**
1. Check Auth0/Okta permissions
2. Reduce required scopes
3. Use optional auth instead

```python
# If scope is too restrictive:
@auth_required(scopes=["admin"])  # Very restrictive

# Consider:
@optional_auth(scopes=["user"])  # More flexible
```

### Issue: Decorator not working

**Possible causes:**
1. Import error
2. Syntax error
3. Decorator applied incorrectly

**Check:**
```python
# Correct:
from fastapps import auth_required

@auth_required(scopes=["user"])
class MyWidget(BaseWidget):
    ...

# Incorrect:
@auth_required["user"]  # Wrong syntax
class MyWidget(BaseWidget):
    ...
```

---

## Related Documentation

- [Server-Wide Auth](./08-AUTH.md) - Configure OAuth for entire server
- [Widget State](./04-STATE.md) - Persist user-specific data
- [API Integration](./06-API.md) - Call authenticated external APIs

---

**Need help?** Check our [GitHub Issues](https://github.com/fastapps-framework/fastapps/issues) or [Discord](https://discord.gg/fastapps).

