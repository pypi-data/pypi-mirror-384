#!/bin/bash

# Quick setup script for FastApps OAuth testing
# This creates a test project with auth-enabled widgets

set -e

echo "========================================="
echo "FastApps OAuth Testing - Quick Setup"
echo "========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "setup.py" ]; then
    echo "❌ Error: Please run this script from the FastApps directory"
    exit 1
fi

# Prompt for Auth0 credentials
echo "📝 Enter your Auth0 configuration:"
echo "(You can get these from https://auth0.com dashboard)"
echo ""

read -p "Auth0 Domain (e.g., your-tenant.us.auth0.com): " AUTH0_DOMAIN
read -p "API Identifier/Audience (e.g., https://fastapps-test.example.com): " AUTH0_AUDIENCE

if [ -z "$AUTH0_DOMAIN" ] || [ -z "$AUTH0_AUDIENCE" ]; then
    echo "❌ Error: Both Auth0 domain and API identifier are required"
    exit 1
fi

# Create test directory
TEST_DIR="../fastapps-auth-test"
echo ""
echo "📁 Creating test project in: $TEST_DIR"

mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install FastApps
echo "📦 Installing FastApps..."
pip install -q --upgrade pip
pip install -q -e ../FastApps
pip install -q httpx PyJWT cryptography

# Initialize project
echo "🏗️  Initializing FastApps project..."
fastapps init auth-test-widgets
cd auth-test-widgets

# Install JS dependencies
echo "📦 Installing JavaScript dependencies..."
npm install --silent

# Create test widgets
echo "🎨 Creating test widgets..."

# 1. Protected widget
fastapps create protected-widget

cat > server/tools/protected_widget_tool.py << 'EOF'
from fastapps import BaseWidget, ConfigDict, auth_required, UserContext
from pydantic import BaseModel
from typing import Dict, Any

class ProtectedWidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    message: str = "Hello"

@auth_required(scopes=["user", "read:data"])
class ProtectedWidgetTool(BaseWidget):
    identifier = "protected-widget"
    title = "Protected Widget"
    description = "Requires authentication with user and read:data scopes"
    input_schema = ProtectedWidgetInput
    invoking = "Loading protected widget..."
    invoked = "Protected widget loaded!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: ProtectedWidgetInput, context=None, user: UserContext = None) -> Dict[str, Any]:
        return {
            "type": "protected",
            "message": f"Hello, {user.claims.get('name', 'User')}!",
            "user_id": user.subject,
            "email": user.claims.get('email', 'N/A'),
            "scopes": user.scopes,
            "permissions": {
                "read": user.has_scope("read:data"),
                "write": user.has_scope("write:data"),
                "admin": user.has_scope("admin"),
            },
            "input": input_data.message,
        }
EOF

# 2. Public widget
fastapps create public-widget

cat > server/tools/public_widget_tool.py << 'EOF'
from fastapps import BaseWidget, ConfigDict, no_auth
from pydantic import BaseModel
from typing import Dict, Any

class PublicWidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

@no_auth
class PublicWidgetTool(BaseWidget):
    identifier = "public-widget"
    title = "Public Widget"
    description = "No authentication required - public access"
    input_schema = PublicWidgetInput
    invoking = "Loading public widget..."
    invoked = "Public widget loaded!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: PublicWidgetInput, context=None, user=None) -> Dict[str, Any]:
        return {
            "type": "public",
            "message": "This is public content - no auth required",
            "authenticated": user.is_authenticated if user else False,
            "access_level": "public",
        }
EOF

# 3. Flexible widget
fastapps create flexible-widget

cat > server/tools/flexible_widget_tool.py << 'EOF'
from fastapps import BaseWidget, ConfigDict, optional_auth, UserContext
from pydantic import BaseModel
from typing import Dict, Any

class FlexibleWidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

@optional_auth(scopes=["user"])
class FlexibleWidgetTool(BaseWidget):
    identifier = "flexible-widget"
    title = "Flexible Widget"
    description = "Works for both authenticated and anonymous users"
    input_schema = FlexibleWidgetInput
    invoking = "Loading flexible widget..."
    invoked = "Flexible widget loaded!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: FlexibleWidgetInput, context=None, user: UserContext = None) -> Dict[str, Any]:
        if user and user.is_authenticated:
            return {
                "type": "flexible",
                "tier": "premium",
                "message": f"Welcome back, {user.claims.get('name', 'User')}!",
                "user_id": user.subject,
                "features": ["basic", "advanced", "export", "share"],
                "personalized": True,
            }
        
        return {
            "type": "flexible",
            "tier": "free",
            "message": "Welcome! Sign in to unlock premium features.",
            "features": ["basic"],
            "personalized": False,
        }
EOF

# Update server/main.py with Auth0 config
cat > server/main.py << EOF
from pathlib import Path
import sys
import importlib
import inspect

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapps import WidgetBuilder, WidgetMCPServer, BaseWidget
import uvicorn

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent / "tools"

def auto_load_tools(build_results):
    tools = []
    for tool_file in TOOLS_DIR.glob("*_tool.py"):
        module_name = tool_file.stem
        try:
            module = importlib.import_module(f"server.tools.{module_name}")
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BaseWidget) and obj is not BaseWidget:
                    tool_identifier = obj.identifier
                    if tool_identifier in build_results:
                        tool_instance = obj(build_results[tool_identifier])
                        tools.append(tool_instance)
                        print(f"✓ {name}")
                    else:
                        print(f"⚠ No build: {tool_identifier}")
        except Exception as e:
            print(f"✗ Error: {tool_file.name}: {e}")
    return tools

# Build widgets
builder = WidgetBuilder(PROJECT_ROOT)
build_results = builder.build_all()
tools = auto_load_tools(build_results)

# Auth0 Configuration
AUTH0_DOMAIN = "${AUTH0_DOMAIN}"
AUTH0_AUDIENCE = "${AUTH0_AUDIENCE}"
NGROK_URL = "https://REPLACE-ME.ngrok-free.app"  # Update after starting ngrok

# Create server with OAuth
server = WidgetMCPServer(
    name="fastapps-auth-test",
    widgets=tools,
    auth_issuer_url=f"https://{AUTH0_DOMAIN}",
    auth_resource_server_url=f"{NGROK_URL}/mcp",
    auth_audience=AUTH0_AUDIENCE,
    auth_required_scopes=["user"],
)

app = server.get_app()

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("FastApps OAuth Test Server")
    print("=" * 60)
    print(f"Auth Provider: {AUTH0_DOMAIN}")
    print(f"Widgets: {len(tools)}")
    print(f"Port: 8001")
    print()
    print("⚠️  IMPORTANT: Start ngrok in another terminal:")
    print("   ngrok http 8001")
    print()
    print("📝 After getting ngrok URL, update NGROK_URL in server/main.py")
    print()
    print("✨ Test Widgets:")
    for tool in tools:
        auth_type = getattr(tool, '_auth_required', None)
        symbol = "🔒" if auth_type is True else "🌐" if auth_type is False else "🔓"
        print(f"   {symbol} {tool.title}")
    print()
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
EOF

# Build widgets
echo "🔨 Building widgets..."
npm run build > /dev/null 2>&1

echo ""
echo "========================================="
echo "✅ Setup Complete!"
echo "========================================="
echo ""
echo "📂 Project created at: $(pwd)"
echo ""
echo "🚀 Next Steps:"
echo ""
echo "1. Start the server (Terminal 1):"
echo "   cd $(pwd)"
echo "   source venv/bin/activate"
echo "   python server/main.py"
echo ""
echo "2. Start ngrok (Terminal 2):"
echo "   ngrok http 8001"
echo ""
echo "3. Copy ngrok URL and update server/main.py:"
echo "   NGROK_URL = \"https://YOUR-URL.ngrok-free.app\""
echo ""
echo "4. Restart server and test in ChatGPT:"
echo "   Settings → Connectors → Add Connector"
echo "   URL: https://YOUR-URL.ngrok-free.app/mcp"
echo ""
echo "📖 Full guide: ../FastApps/OAUTH_TESTING_GUIDE.md"
echo ""
echo "✨ Test widgets created:"
echo "   🔒 protected-widget - Requires auth (user + read:data scopes)"
echo "   🌐 public-widget - No auth required"
echo "   🔓 flexible-widget - Optional auth (premium vs free)"
echo ""
echo "========================================="

