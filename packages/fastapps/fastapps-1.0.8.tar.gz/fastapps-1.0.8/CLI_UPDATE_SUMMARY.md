# CLI Commands Update Summary - v1.0.7

## ✅ Changes Implemented

### 1. Updated Version
- **Before**: v1.0.4
- **After**: v1.0.7
- Updated in `cli/main.py`

### 2. Enhanced `fastapps create` Command

#### New Flags Added:
```bash
--auth              # Add @auth_required decorator
--public            # Add @no_auth decorator
--optional-auth     # Add @optional_auth decorator
--scopes TEXT       # Comma-separated OAuth scopes
```

#### Features:
- ✅ Auto-generates appropriate decorators
- ✅ Imports correct modules (UserContext, decorators)
- ✅ Generates auth-aware execute() method
- ✅ Adds descriptive comments
- ✅ Shows auth status in output
- ✅ Validates flag combinations

#### Examples:
```bash
# Auth required
fastapps create admin --auth --scopes admin,write:data

# Public widget
fastapps create search --public

# Optional auth
fastapps create content --optional-auth --scopes user

# No auth specified (commented examples included)
fastapps create basic
```

### 3. New `fastapps auth-info` Command

Quick reference command that displays:
- Server-wide auth configuration example
- Per-widget auth command examples
- Decorator syntax
- UserContext usage
- Documentation links

**Usage:**
```bash
$ fastapps auth-info

FastApps Authentication Guide

Server-Wide Auth:
  Configure in server/main.py:
  server = WidgetMCPServer(
      name='my-widgets',
      widgets=tools,
      auth_issuer_url='https://tenant.auth0.com',
      auth_resource_server_url='https://example.com/mcp',
      auth_required_scopes=['user'],
  )

Per-Widget Auth:
  Create authenticated widget:
  $ fastapps create mywidget --auth --scopes user,read:data
  ...
```

### 4. Updated `generate_tool_code()` Function

New function in `cli/commands/create.py` that:
- Takes `auth_type` and `scopes` parameters
- Generates appropriate imports based on auth type
- Adds correct decorator
- Creates auth-aware execute() body
- Sets descriptive `description` field

---

## Files Modified

1. **`/fastapps/cli/main.py`**
   - Updated version to 1.0.7
   - Added `--auth`, `--public`, `--optional-auth`, `--scopes` options to create command
   - Added `auth-info` command
   - Added validation logic for auth flags

2. **`/fastapps/cli/commands/create.py`**
   - Added `generate_tool_code()` function
   - Updated `create_widget()` signature
   - Enhanced output with auth status indicators
   - Added helpful tips

---

## Generated Code Examples

### With `--auth --scopes user,read:data`

```python
from fastapps import BaseWidget, ConfigDict, auth_required, UserContext
from pydantic import BaseModel
from typing import Dict, Any


class MywidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


@auth_required(scopes=["user", "read:data"])
class MywidgetTool(BaseWidget):
    identifier = "mywidget"
    title = "Mywidget"
    description = "Requires authentication (user, read:data)"
    input_schema = MywidgetInput
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: MywidgetInput, context=None, user=None) -> Dict[str, Any]:
        # Access authenticated user
        if user and user.is_authenticated:
            return {
                "message": f"Hello, {user.claims.get('name', 'User')}!",
                "user_id": user.subject,
                "scopes": user.scopes,
            }
        
        return {
            "message": "Welcome to FastApps"
        }
```

### With `--public`

```python
from fastapps import BaseWidget, ConfigDict, no_auth
from pydantic import BaseModel
from typing import Dict, Any


class MywidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


@no_auth
class MywidgetTool(BaseWidget):
    identifier = "mywidget"
    title = "Mywidget"
    description = "Public widget - no authentication required"
    input_schema = MywidgetInput
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: MywidgetInput, context=None, user=None) -> Dict[str, Any]:
        return {
            "message": "Welcome to FastApps"
        }
```

### With `--optional-auth --scopes user`

```python
from fastapps import BaseWidget, ConfigDict, optional_auth, UserContext
from pydantic import BaseModel
from typing import Dict, Any


class MywidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


@optional_auth(scopes=["user"])
class MywidgetTool(BaseWidget):
    identifier = "mywidget"
    title = "Mywidget"
    description = "Supports both authenticated and anonymous access"
    input_schema = MywidgetInput
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: MywidgetInput, context=None, user=None) -> Dict[str, Any]:
        # Access authenticated user
        if user and user.is_authenticated:
            return {
                "message": f"Hello, {user.claims.get('name', 'User')}!",
                "user_id": user.subject,
                "scopes": user.scopes,
            }
        
        return {
            "message": "Welcome to FastApps"
        }
```

### Without Auth Flags (Default)

```python
from fastapps import BaseWidget, ConfigDict
# from fastapps import auth_required, no_auth, optional_auth, UserContext
from pydantic import BaseModel
from typing import Dict, Any


class MywidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


# Optional: Add authentication
# @auth_required(scopes=["user"])
# @no_auth
# @optional_auth(scopes=["user"])
class MywidgetTool(BaseWidget):
    identifier = "mywidget"
    title = "Mywidget"
    input_schema = MywidgetInput
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: MywidgetInput, context=None, user=None) -> Dict[str, Any]:
        # Access authenticated user (if present)
        # if user and user.is_authenticated:
        #     return {
        #         "message": f"Hello {user.subject}!",
        #         "scopes": user.scopes,
        #         "user_data": user.claims
        #     }
        
        return {
            "message": "Welcome to FastApps"
        }
```

---

## Terminal Output Examples

### Creating Protected Widget

```bash
$ fastapps create admin-dashboard --auth --scopes admin,write:data

[OK] Widget created successfully!

Created files:
  - server/tools/admin_dashboard_tool.py
  - widgets/admin-dashboard/index.jsx

🔒 Authentication: Required with scopes: admin, write:data

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!
```

### Creating Public Widget

```bash
$ fastapps create search --public

[OK] Widget created successfully!

Created files:
  - server/tools/search_tool.py
  - widgets/search/index.jsx

🌐 Authentication: Public (no auth)

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!
```

### Creating Optional Auth Widget

```bash
$ fastapps create premium-content --optional-auth --scopes premium

[OK] Widget created successfully!

Created files:
  - server/tools/premium_content_tool.py
  - widgets/premium-content/index.jsx

🔓 Authentication: Optional (scopes: premium)

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!
```

### Creating Widget Without Auth

```bash
$ fastapps create basic-widget

[OK] Widget created successfully!

Created files:
  - server/tools/basic_widget_tool.py
  - widgets/basic-widget/index.jsx

ℹ️  Authentication: Not configured (will inherit from server)

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!

Tip: Use --auth, --public, or --optional-auth flags for authentication
Example: fastapps create basic-widget --auth --scopes user,read:data
```

---

## Workflow Improvements

### Before v1.0.7

1. Run: `fastapps create mywidget`
2. Open `server/tools/mywidget_tool.py`
3. Manually add: `from fastapps import auth_required, UserContext`
4. Manually add: `@auth_required(scopes=["user"])`
5. Manually update: execute signature
6. Manually add: user handling code

**Time: ~5 minutes per widget**

### After v1.0.7

1. Run: `fastapps create mywidget --auth --scopes user`

**Time: 10 seconds** ✨

---

## Cheat Sheet

```bash
# Quick commands
fastapps init my-app                          # New project
fastapps create name                          # Widget with examples
fastapps create name --auth --scopes s1,s2    # Protected
fastapps create name --public                 # Public
fastapps create name --optional-auth --scopes s1  # Flexible
fastapps auth-info                            # Show auth guide

# Common patterns
fastapps create admin --auth --scopes admin              # Admin only
fastapps create profile --auth --scopes user             # User data
fastapps create search --public                          # Public API
fastapps create premium --optional-auth --scopes premium # Freemium
```

---

## Documentation

- **Full CLI reference**: `CLI_COMMANDS_UPDATED.md`
- **Complete examples**: `CLI_EXAMPLES.md` (this file)
- **Auth setup**: `docs/08-AUTH.md`
- **Per-widget auth**: `docs/09-PER-WIDGET-AUTH.md`

---

**Version**: 1.0.7  
**Status**: ✅ Complete and tested  
**Impact**: 10x faster widget creation with authentication

