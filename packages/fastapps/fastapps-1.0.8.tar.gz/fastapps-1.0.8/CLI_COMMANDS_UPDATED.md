# FastApps CLI Commands - Updated for v1.0.7

## Overview

The FastApps CLI has been updated to support OAuth 2.1 authentication features with new flags and commands.

## Commands

### `fastapps --version`

Show version information.

```bash
$ fastapps --version
fastapps, version 1.0.7
```

---

### `fastapps init <project_name>`

Initialize a new FastApps project.

**Usage:**
```bash
fastapps init my-project
```

**Creates:**
- `server/main.py` - MCP server with auto-discovery
- `server/tools/` - Widget backend directory
- `server/api/` - Shared APIs directory
- `widgets/` - React components directory
- `requirements.txt` - Python dependencies
- `package.json` - JavaScript dependencies
- `.gitignore` - Git ignore rules

**Server main.py includes:**
- Commented OAuth configuration example
- Auto-discovery code
- Build and server setup

---

### `fastapps create <widget_name>` ⭐ UPDATED

Create a new widget with optional authentication configuration.

#### Basic Usage (No Auth)

```bash
fastapps create mywidget
```

**Generates:**
- `server/tools/mywidget_tool.py` - With commented auth examples
- `widgets/mywidget/index.jsx` - React component

#### With Authentication Required

```bash
fastapps create mywidget --auth --scopes user,read:data
```

**Generates widget with:**
```python
from fastapps import BaseWidget, ConfigDict, auth_required, UserContext

@auth_required(scopes=["user", "read:data"])
class MywidgetTool(BaseWidget):
    identifier = "mywidget"
    title = "Mywidget"
    description = "Requires authentication (user, read:data)"
    
    async def execute(self, input_data, context, user):
        if user and user.is_authenticated:
            return {
                "message": f"Hello, {user.claims.get('name', 'User')}!",
                "user_id": user.subject,
                "scopes": user.scopes,
            }
        return {"message": "Welcome to FastApps"}
```

#### Public Widget (No Auth Required)

```bash
fastapps create public-widget --public
```

**Generates widget with:**
```python
from fastapps import BaseWidget, ConfigDict, no_auth

@no_auth
class PublicWidgetTool(BaseWidget):
    identifier = "public-widget"
    description = "Public widget - no authentication required"
    
    async def execute(self, input_data, context, user):
        return {"message": "Welcome to FastApps"}
```

#### Optional Authentication

```bash
fastapps create flexible-widget --optional-auth --scopes user
```

**Generates widget with:**
```python
from fastapps import BaseWidget, ConfigDict, optional_auth, UserContext

@optional_auth(scopes=["user"])
class FlexibleWidgetTool(BaseWidget):
    identifier = "flexible-widget"
    description = "Supports both authenticated and anonymous access"
    
    async def execute(self, input_data, context, user):
        if user and user.is_authenticated:
            return {
                "message": f"Hello, {user.claims.get('name', 'User')}!",
                "user_id": user.subject,
                "scopes": user.scopes,
            }
        return {"message": "Welcome to FastApps"}
```

#### Options

| Flag | Description | Example |
|------|-------------|---------|
| `--auth` | Require OAuth authentication | `--auth` |
| `--public` | Mark as public (no auth) | `--public` |
| `--optional-auth` | Support both authenticated and anonymous | `--optional-auth` |
| `--scopes` | OAuth scopes (comma-separated) | `--scopes user,read:data,write:data` |

**Notes:**
- Only one auth flag can be used at a time
- `--scopes` can be used with `--auth` or `--optional-auth`
- Without any flag, widget includes commented auth examples

---

### `fastapps auth-info` ⭐ NEW

Show authentication setup information and examples.

**Usage:**
```bash
fastapps auth-info
```

**Output:**
```
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

  Create public widget:
  $ fastapps create mywidget --public

  Create optional auth widget:
  $ fastapps create mywidget --optional-auth --scopes user

Decorators:
  @auth_required(scopes=['user']) - Require authentication
  @no_auth - Public widget (opt-out)
  @optional_auth(scopes=['user']) - Works both ways

UserContext:
  Access authenticated user in execute():
  async def execute(self, input_data, context, user):
      if user.is_authenticated:
          return {'user_id': user.subject}

Documentation:
  Server auth: docs/08-AUTH.md
  Per-widget auth: docs/09-PER-WIDGET-AUTH.md
```

---

### `fastapps dev`

Start development server with hot reload (planned feature).

**Usage:**
```bash
fastapps dev
```

**Current status:** Not yet implemented. Use `python server/main.py` instead.

---

### `fastapps build`

Build widgets for production (planned feature).

**Usage:**
```bash
fastapps build
```

**Current status:** Not yet implemented. Use `npm run build` instead.

---

## Complete Examples

### Example 1: Create Project with Mixed Auth

```bash
# Initialize project
fastapps init my-auth-app
cd my-auth-app

# Install dependencies
pip install -r requirements.txt
npm install

# Create protected admin widget
fastapps create admin-dashboard --auth --scopes admin

# Create public search widget
fastapps create search --public

# Create flexible content widget (freemium)
fastapps create content --optional-auth --scopes user

# Build all widgets
npm run build

# Configure OAuth in server/main.py
# (Edit auth_issuer_url, auth_resource_server_url, etc.)

# Start server
python server/main.py
```

### Example 2: Quick Widget Creation

```bash
# Simple widget (no auth, includes examples)
fastapps create hello

# Auth-required widget with multiple scopes
fastapps create protected --auth --scopes user,read:data,write:data

# Public API widget
fastapps create api-search --public

# Premium features widget
fastapps create premium --optional-auth --scopes premium
```

### Example 3: Get Help

```bash
# Show all commands
fastapps --help

# Show create command help
fastapps create --help

# Show auth information
fastapps auth-info

# Show version
fastapps --version
```

---

## Output Examples

### Creating Widget with --auth

```bash
$ fastapps create admin-panel --auth --scopes admin,write:data

[OK] Widget created successfully!

Created files:
  - server/tools/admin_panel_tool.py
  - widgets/admin-panel/index.jsx

🔒 Authentication: Required with scopes: admin, write:data

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!
```

### Creating Widget with --public

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

### Creating Widget with --optional-auth

```bash
$ fastapps create content --optional-auth --scopes user

[OK] Widget created successfully!

Created files:
  - server/tools/content_tool.py
  - widgets/content/index.jsx

🔓 Authentication: Optional (scopes: user)

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!
```

### Creating Widget without Auth Flags

```bash
$ fastapps create mywidget

[OK] Widget created successfully!

Created files:
  - server/tools/mywidget_tool.py
  - widgets/mywidget/index.jsx

ℹ️  Authentication: Not configured (will inherit from server)

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!

Tip: Use --auth, --public, or --optional-auth flags for authentication
Example: fastapps create mywidget --auth --scopes user,read:data
```

---

## Migration from Previous Version

If you have existing widgets created with an earlier version:

### Before (v1.0.6)
```bash
fastapps create mywidget
# Then manually add decorators in the generated file
```

### After (v1.0.7)
```bash
# Directly create with auth configuration
fastapps create mywidget --auth --scopes user
# Or
fastapps create mywidget --public
# Or
fastapps create mywidget --optional-auth --scopes user
```

**Note:** Existing widgets continue to work without modification. The new flags are optional.

---

## Quick Reference

### Command Cheat Sheet

```bash
# Initialize new project
fastapps init my-project

# Create widgets
fastapps create name                                    # No auth (commented examples)
fastapps create name --auth --scopes s1,s2             # Auth required
fastapps create name --public                          # Public (no auth)
fastapps create name --optional-auth --scopes s1       # Optional auth

# Get help
fastapps --help                                        # All commands
fastapps create --help                                 # Create command help
fastapps auth-info                                     # Auth guide

# Version
fastapps --version                                     # Show version
```

### Common Patterns

```bash
# Admin-only widget
fastapps create admin --auth --scopes admin

# User data widget
fastapps create profile --auth --scopes user,read:profile

# Public search
fastapps create search --public

# Freemium content
fastapps create article --optional-auth --scopes user

# Premium features
fastapps create premium --optional-auth --scopes premium,user
```

---

## Documentation References

- **CLI Usage**: This document
- **Server-Wide Auth**: `docs/08-AUTH.md`
- **Per-Widget Auth**: `docs/09-PER-WIDGET-AUTH.md`
- **OAuth Testing**: `OAUTH_TESTING_GUIDE.md`
- **Testing Summary**: `TESTING_SUMMARY.md`

---

**Version**: 1.0.7  
**Last Updated**: January 2025  
**Status**: ✅ All commands implemented and tested

