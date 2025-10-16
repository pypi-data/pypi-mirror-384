"""Initialize new FastApps project command."""

from pathlib import Path
from rich.console import Console

console = Console()

# Server main.py template
SERVER_MAIN_TEMPLATE = '''from pathlib import Path
import sys
import importlib
import inspect

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import FastApps framework
from fastapps import WidgetBuilder, WidgetMCPServer, BaseWidget
import uvicorn

PROJECT_ROOT = Path(__file__).parent.parent
TOOLS_DIR = Path(__file__).parent / "tools"

def auto_load_tools(build_results):
    """Automatically discover and load all widget tools."""
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
                        print(f"[OK] Loaded tool: {name} (identifier: {tool_identifier})")
                    else:
                        print(f"[WARNING] Warning: No build result found for tool '{tool_identifier}'")
        except Exception as e:
            print(f"[ERROR] Error loading {tool_file.name}: {e}")
    return tools

# Build all widgets
builder = WidgetBuilder(PROJECT_ROOT)
build_results = builder.build_all()

# Auto-load and register tools
tools = auto_load_tools(build_results)

# Create MCP server
server = WidgetMCPServer(name="my-widgets", widgets=tools)
app = server.get_app()

if __name__ == "__main__":
    print(f"\\n[START] Starting server with {len(tools)} tools")
    uvicorn.run(app, host="0.0.0.0", port=8001)
'''

REQUIREMENTS_TXT = '''fastapps>=1.0.1
httpx>=0.28.0
'''

def get_package_json(project_name: str) -> str:
    """Generate package.json content."""
    import json
    return json.dumps({
        "name": project_name,
        "version": "1.0.0",
        "type": "module",
        "description": "Floydr ChatGPT widgets project",
        "scripts": {
            "build": "npx tsx node_modules/chatjs-hooks/build-all.mts"
        },
        "dependencies": {
            "chatjs-hooks": "^1.0.0",
            "react": "^18.3.1",
            "react-dom": "^18.3.1"
        },
        "devDependencies": {
            "@vitejs/plugin-react": "^4.3.4",
            "fast-glob": "^3.3.2",
            "tsx": "^4.19.2",
            "typescript": "^5.7.2",
            "vite": "^6.0.5"
        }
    }, indent=2)

PROJECT_README = '''# {project_name}

ChatGPT widgets built with [FastApps](https://pypi.org/project/fastapps/).

## Quick Start

### 1. Install Dependencies

```bash
# Python
pip install -r requirements.txt

# JavaScript
npm install
```

### 2. Create Your First Widget

```bash
python -m fastapps.cli.main create mywidget
```

### 3. Build and Run

```bash
# Build widgets
npm run build

# Start server
python server/main.py
```

## Project Structure

```
{project_name}/
├── server/
│   ├── main.py              # Server (auto-discovery)
│   └── tools/               # Widget backends
│       └── *_tool.py        # Your widget logic
│
├── widgets/                 # Widget frontends
│   └── */
│       └── index.jsx        # Your React components
│
├── assets/                  # Built widgets (auto-generated)
├── requirements.txt
└── package.json
```

## Creating Widgets

```bash
# Generate new widget
python -m floydr.cli.main create mywidget

# Then edit:
# - server/tools/mywidget_tool.py   (backend)
# - widgets/mywidget/index.jsx      (frontend)

# Build and run
npm run build
python server/main.py
```

## Learn More

- **FastApps Framework**: https://pypi.org/project/fastapps/
- **ChatJS Hooks**: https://www.npmjs.com/package/chatjs-hooks
- **Documentation**: https://github.com/fastapps-framework/fastapps

## License

MIT
'''

GITIGNORE = '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg
venv/
ENV/
env/
.venv

# JavaScript
node_modules/
npm-debug.log*
*.log
dist/
.cache/

# Build outputs
assets/
build-all.mts

# IDEs
.vscode/
.idea/
*.swp
.DS_Store
'''


def init_project(project_name: str):
    """Initialize a new Floydr project."""
    
    project_path = Path(project_name)
    
    # Check if directory exists
    if project_path.exists():
        console.print(f"[red][ERROR] Directory '{project_name}' already exists[/red]")
        return False
    
    console.print(f"[green]Creating FastApps project: [bold]{project_name}[/bold][/green]\n")
    
    try:
        # Create directory structure
        console.print("Creating directory structure...")
        (project_path / "server" / "tools").mkdir(parents=True)
        (project_path / "server" / "api").mkdir(parents=True)
        (project_path / "widgets").mkdir(parents=True)
        
        # Create empty __init__.py files
        console.print("Creating Python modules...")
        (project_path / "server" / "__init__.py").write_text("")
        (project_path / "server" / "tools" / "__init__.py").write_text("")
        (project_path / "server" / "api" / "__init__.py").write_text("")
        
        # Create server/main.py
        console.print("Creating server...")
        (project_path / "server" / "main.py").write_text(SERVER_MAIN_TEMPLATE)
        
        # Create requirements.txt
        console.print("Creating requirements.txt...")
        (project_path / "requirements.txt").write_text(REQUIREMENTS_TXT)
        
        # Create package.json
        console.print("Creating package.json...")
        (project_path / "package.json").write_text(get_package_json(project_name))
        
        # Create README.md
        console.print("Creating README.md...")
        readme_content = PROJECT_README.format(project_name=project_name)
        (project_path / "README.md").write_text(readme_content)
        
        # Create .gitignore
        console.print("Creating .gitignore...")
        (project_path / ".gitignore").write_text(GITIGNORE)
        
        console.print(f"\n[green][OK] Project '{project_name}' created successfully![/green]")
        console.print(f"\n[cyan]Next steps:[/cyan]")
        console.print(f"  [bold]cd {project_name}[/bold]")
        console.print(f"  [bold]pip install -r requirements.txt[/bold]")
        console.print(f"  [bold]npm install[/bold]")
        console.print(f"  [bold]fastapps create mywidget[/bold]")
        console.print(f"  [bold]npm run build[/bold]")
        console.print(f"  [bold]python server/main.py[/bold]")
        console.print(f"\n[green]Happy building![/green]\n")
        
        return True
        
    except Exception as e:
        console.print(f"[red][ERROR] Error creating project: {e}[/red]")
        return False

