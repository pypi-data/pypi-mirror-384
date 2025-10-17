# FastApps CLI - Complete Examples

## ✨ What's New in v1.0.7

### Enhanced `create` Command
- `--auth` flag to require authentication
- `--public` flag to mark as public
- `--optional-auth` flag for flexible auth
- `--scopes` flag to specify OAuth scopes
- Auto-generates appropriate decorators and code

### New `auth-info` Command
- Quick reference for authentication setup
- Shows examples and documentation links

### Updated Version
- Now reports v1.0.7

---

## Command Reference

### Help Output

```bash
$ fastapps --help

Usage: fastapps [OPTIONS] COMMAND [ARGS]...

  FastApps - ChatGPT Widget Framework
  
  Build interactive ChatGPT widgets with zero boilerplate.
  Supports OAuth 2.1 authentication for secure widgets.

Options:
  --version   Show the version and exit.
  --help      Show this message and exit.

Commands:
  init        Initialize a new FastApps project.
  create      Create a new widget with tool and component files.
  dev         Start development server with hot reload.
  build       Build widgets for production.
  auth-info   Show authentication setup information.
```

### Create Command Help

```bash
$ fastapps create --help

Usage: fastapps create [OPTIONS] WIDGET_NAME

  Create a new widget with tool and component files.
  
  Examples:
      fastapps create mywidget
      fastapps create mywidget --auth --scopes user,read:data
      fastapps create mywidget --public
      fastapps create mywidget --optional-auth --scopes user
  
  Authentication options:
      --auth: Require OAuth authentication
      --public: Mark as public (no auth)
      --optional-auth: Support both authenticated and anonymous
      --scopes: OAuth scopes to require

Options:
  --auth              Add auth_required decorator to widget
  --public            Add no_auth decorator (public widget)
  --optional-auth     Add optional_auth decorator
  --scopes TEXT       OAuth scopes (comma-separated, e.g., 'user,read:data')
  --help              Show this message and exit.
```

---

## Usage Examples

### Example 1: E-commerce App

```bash
# Initialize project
fastapps init shop-widgets
cd shop-widgets
pip install -r requirements.txt
npm install

# Public product catalog
fastapps create product-catalog --public

# User cart (requires auth)
fastapps create shopping-cart --auth --scopes user,read:cart

# Checkout (requires auth + write)
fastapps create checkout --auth --scopes user,write:orders

# Product reviews (optional auth - better when logged in)
fastapps create reviews --optional-auth --scopes user

# Admin panel
fastapps create admin-panel --auth --scopes admin

# Build and run
npm run build
python server/main.py
```

**Result:** 5 widgets with appropriate auth:
- 🌐 product-catalog - Public
- 🔒 shopping-cart - Auth required
- 🔒 checkout - Auth required
- 🔓 reviews - Optional auth
- 🔒 admin-panel - Admin only

### Example 2: Content Management System

```bash
fastapps init cms-widgets
cd cms-widgets
pip install -r requirements.txt && npm install

# Public article viewer
fastapps create article-viewer --public

# Article editor (requires auth)
fastapps create article-editor --auth --scopes user,write:articles

# Comment system (better when authenticated)
fastapps create comments --optional-auth --scopes user

# Media library (requires auth)
fastapps create media-library --auth --scopes user,read:media

# Analytics dashboard (admin only)
fastapps create analytics --auth --scopes admin

npm run build
# Configure OAuth in server/main.py
python server/main.py
```

### Example 3: SaaS Dashboard

```bash
fastapps init saas-app
cd saas-app
pip install -r requirements.txt && npm install

# Public landing page
fastapps create landing --public

# User dashboard (requires auth)
fastapps create dashboard --auth --scopes user

# Settings panel (requires auth)
fastapps create settings --auth --scopes user,write:profile

# API key manager (requires auth)
fastapps create api-keys --auth --scopes user,write:keys

# Billing (requires auth + billing scope)
fastapps create billing --auth --scopes user,read:billing

# Team management (admin)
fastapps create team --auth --scopes admin,write:team

npm run build
python server/main.py
```

---

## Step-by-Step Walkthrough

### Creating Your First Authenticated Widget

```bash
# 1. Create project
fastapps init my-app
cd my-app

# 2. Install dependencies
pip install -r requirements.txt
npm install

# 3. Create authenticated widget
fastapps create user-profile --auth --scopes user,read:profile
```

**Output:**
```
[OK] Widget created successfully!

Created files:
  - server/tools/user_profile_tool.py
  - widgets/user-profile/index.jsx

🔒 Authentication: Required with scopes: user, read:profile

Next steps:
  1. npm run build
  2. python server/main.py

Your widget will be automatically discovered by FastApps!
```

**Generated code** (`server/tools/user_profile_tool.py`):
```python
from fastapps import BaseWidget, ConfigDict, auth_required, UserContext
from pydantic import BaseModel
from typing import Dict, Any


class UserProfileInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


@auth_required(scopes=["user", "read:profile"])
class UserProfileTool(BaseWidget):
    identifier = "user-profile"
    title = "User Profile"
    description = "Requires authentication (user, read:profile)"
    input_schema = UserProfileInput
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: UserProfileInput, context=None, user=None) -> Dict[str, Any]:
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

### 4. Build and Run

```bash
# Build widgets
npm run build

# Configure OAuth in server/main.py
# Edit: auth_issuer_url, auth_resource_server_url, auth_audience

# Start server
python server/main.py

# In another terminal: expose with ngrok
ngrok http 8001

# Add to ChatGPT
# Settings → Connectors → Add Connector
# URL: https://YOUR-URL.ngrok-free.app/mcp
```

---

## Comparison: Before vs After

### Before v1.0.7

```bash
# Create widget
fastapps create mywidget

# Manually edit server/tools/mywidget_tool.py to add:
# - Import auth_required
# - Add @auth_required decorator
# - Update execute signature
# - Add user context handling
```

### After v1.0.7

```bash
# Create widget with auth in one command
fastapps create mywidget --auth --scopes user,read:data

# Everything is generated automatically!
```

**Time saved:** ~5 minutes per widget

---

## Tips & Tricks

### 1. Use auth-info for Quick Reference

```bash
fastapps auth-info
```

Shows all auth patterns and examples without needing to check docs.

### 2. Specify Scopes Clearly

```bash
# Good: Clear, specific scopes
fastapps create editor --auth --scopes user,write:documents

# Also valid: Single scope
fastapps create viewer --auth --scopes user
```

### 3. Public by Default for Discovery

```bash
# For APIs or search, mark as public
fastapps create api-search --public
```

### 4. Optional Auth for Freemium

```bash
# Unlock features when user authenticates
fastapps create content --optional-auth --scopes user
```

### 5. Check Generated Code

After creating, always review the generated files:
```bash
cat server/tools/mywidget_tool.py
# Verify decorator and scopes are correct
```

---

## Error Handling

### Error: Multiple auth flags

```bash
$ fastapps create test --auth --public

Error: Only one auth option allowed (--auth, --public, or --optional-auth)
```

**Solution:** Use only one auth flag.

### Error: Scopes without auth flag

```bash
$ fastapps create test --scopes user

[WARNING] --scopes has no effect without --auth or --optional-auth
```

**Solution:** Add `--auth` or `--optional-auth`.

---

## Documentation

- **This guide**: Complete CLI examples
- **Server auth**: `docs/08-AUTH.md`
- **Per-widget auth**: `docs/09-PER-WIDGET-AUTH.md`
- **Quick start**: `README.md`
- **OAuth testing**: `OAUTH_TESTING_GUIDE.md`

---

**Ready to build?**

```bash
fastapps init my-app
cd my-app
pip install -r requirements.txt && npm install
fastapps create mywidget --auth --scopes user
npm run build
python server/main.py
```

