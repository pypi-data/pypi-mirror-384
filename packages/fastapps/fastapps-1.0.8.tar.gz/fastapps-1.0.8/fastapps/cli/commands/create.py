"""Create widget command."""

from pathlib import Path
from rich.console import Console

console = Console()

def generate_tool_code(class_name: str, identifier: str, title: str, auth_type: str = None, scopes: list = None) -> str:
    """Generate tool code with optional authentication."""
    
    # Base imports
    imports = "from fastapps import BaseWidget, ConfigDict"
    
    # Add auth imports if needed
    if auth_type == "required":
        imports += ", auth_required, UserContext"
    elif auth_type == "none":
        imports += ", no_auth"
    elif auth_type == "optional":
        imports += ", optional_auth, UserContext"
    else:
        # Include commented examples
        imports += "\n# from fastapps import auth_required, no_auth, optional_auth, UserContext"
    
    imports += "\nfrom pydantic import BaseModel\nfrom typing import Dict, Any"
    
    # Generate decorator
    decorator = ""
    if auth_type == "required":
        scope_str = f"[{', '.join(repr(s) for s in scopes)}]" if scopes else "[]"
        decorator = f"@auth_required(scopes={scope_str})"
    elif auth_type == "none":
        decorator = "@no_auth"
    elif auth_type == "optional":
        scope_str = f"[{', '.join(repr(s) for s in scopes)}]" if scopes else "[]"
        decorator = f"@optional_auth(scopes={scope_str})"
    else:
        # Commented examples
        decorator = """# Optional: Add authentication
# @auth_required(scopes=["user"])
# @no_auth
# @optional_auth(scopes=["user"])"""
    
    # Generate execute body based on auth type
    if auth_type in ["required", "optional"]:
        execute_body = '''        # Access authenticated user
        if user and user.is_authenticated:
            return {
                "message": f"Hello, {user.claims.get('name', 'User')}!",
                "user_id": user.subject,
                "scopes": user.scopes,
            }
        
        return {
            "message": "Welcome to FastApps"
        }'''
    else:
        execute_body = '''        return {
            "message": "Welcome to FastApps"
        }'''
    
    # Generate description based on auth type
    if auth_type == "required":
        scope_desc = f" ({', '.join(scopes)})" if scopes else ""
        description = f"Requires authentication{scope_desc}"
    elif auth_type == "none":
        description = "Public widget - no authentication required"
    elif auth_type == "optional":
        description = "Supports both authenticated and anonymous access"
    else:
        description = ""
    
    return f'''{imports}


class {class_name}Input(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


{decorator}
class {class_name}Tool(BaseWidget):
    identifier = "{identifier}"
    title = "{title}"{"" if not description else f'''
    description = "{description}"'''}
    input_schema = {class_name}Input
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {{
        "connect_domains": [],
        "resource_domains": []
    }}
    
    async def execute(self, input_data: {class_name}Input, context=None, user=None) -> Dict[str, Any]:
{execute_body}
'''

TOOL_TEMPLATE = '''from fastapps import BaseWidget, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

# Optional: Add per-widget authentication
# from fastapps import auth_required, no_auth, optional_auth


class {ClassName}Input(BaseModel):
    model_config = ConfigDict(populate_by_name=True)


# Optional: Require authentication for this widget
# @auth_required(scopes=["user"])
# Or make it explicitly public:
# @no_auth
# Or support both authenticated and anonymous:
# @optional_auth(scopes=["user"])
class {ClassName}Tool(BaseWidget):
    identifier = "{identifier}"
    title = "{title}"
    input_schema = {ClassName}Input
    invoking = "Loading widget..."
    invoked = "Widget ready!"
    
    widget_csp = {{
        "connect_domains": [],
        "resource_domains": []
    }}
    
    async def execute(self, input_data: {ClassName}Input, context=None, user=None) -> Dict[str, Any]:
        # Access authenticated user (if present)
        # if user and user.is_authenticated:
        #     return {{
        #         "message": f"Hello {{user.subject}}!",
        #         "scopes": user.scopes,
        #         "user_data": user.claims
        #     }}
        
        return {{
            "message": "Welcome to FastApps"
        }}
'''

WIDGET_TEMPLATE = '''import React from 'react';
import {{ useWidgetProps }} from 'fastapps';

export default function {ClassName}() {{
  const props = useWidgetProps();
  
  return (
    <div style={{{{
      background: '#000',
      color: '#fff',
      padding: '40px',
      textAlign: 'center',
      borderRadius: '8px',
      fontFamily: 'monospace'
    }}}}>
      <h1>{{props.message || 'Welcome to FastApps'}}</h1>
    </div>
  );
}}
'''


def create_widget(name: str, auth_type: str = None, scopes: list = None):
    """
    Create a new widget with tool and component files.
    
    Args:
        name: Widget name
        auth_type: Authentication type ('required', 'none', 'optional', or None)
        scopes: List of OAuth scopes
    """
    
    # Convert name to proper formats
    identifier = name.lower().replace('-', '_').replace(' ', '_')
    class_name = ''.join(word.capitalize() for word in identifier.split('_'))
    title = ' '.join(word.capitalize() for word in identifier.split('_'))
    
    # Paths
    tool_dir = Path("server/tools")
    widget_dir = Path("widgets") / identifier
    
    tool_file = tool_dir / f"{identifier}_tool.py"
    widget_file = widget_dir / "index.jsx"
    
    # Check if already exists
    if tool_file.exists():
        console.print(f"[yellow][WARNING] Tool already exists: {tool_file}[/yellow]")
        return False
    
    if widget_file.exists():
        console.print(f"[yellow][WARNING] Widget already exists: {widget_file}[/yellow]")
        return False
    
    # Create directories
    tool_dir.mkdir(parents=True, exist_ok=True)
    widget_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate files with auth configuration
    tool_content = generate_tool_code(
        class_name=class_name,
        identifier=identifier,
        title=title,
        auth_type=auth_type,
        scopes=scopes
    )
    
    widget_content = WIDGET_TEMPLATE.format(
        ClassName=class_name
    )
    
    # Write files
    tool_file.write_text(tool_content)
    widget_file.write_text(widget_content)
    
    console.print(f"\n[green][OK] Widget created successfully![/green]")
    console.print(f"\n[cyan]Created files:[/cyan]")
    console.print(f"  - {tool_file}")
    console.print(f"  - {widget_file}")
    
    # Show auth status
    if auth_type == "required":
        scope_str = f" with scopes: {', '.join(scopes)}" if scopes else ""
        console.print(f"\n[yellow]🔒 Authentication: Required{scope_str}[/yellow]")
    elif auth_type == "none":
        console.print(f"\n[yellow]🌐 Authentication: Public (no auth)[/yellow]")
    elif auth_type == "optional":
        scope_str = f" (scopes: {', '.join(scopes)})" if scopes else ""
        console.print(f"\n[yellow]🔓 Authentication: Optional{scope_str}[/yellow]")
    else:
        console.print(f"\n[yellow]ℹ️  Authentication: Not configured (will inherit from server)[/yellow]")
    
    console.print(f"\n[yellow]Next steps:[/yellow]")
    console.print(f"  1. npm run build")
    console.print(f"  2. python server/main.py")
    console.print(f"\n[green]Your widget will be automatically discovered by FastApps![/green]")
    
    if not auth_type:
        console.print(f"\n[dim]Tip: Use --auth, --public, or --optional-auth flags for authentication[/dim]")
        console.print(f"[dim]Example: fastapps create {name} --auth --scopes user,read:data[/dim]")
    
    console.print()
    
    return True

