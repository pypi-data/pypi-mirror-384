# Complete Project Setup

This guide shows you exactly what files you need to create for a new FastApps project.

## Initial Project Structure

```bash
my-chatgpt-widgets/
├── server/
│   ├── __init__.py
│   ├── main.py
│   ├── tools/
│   │   └── __init__.py
│   └── api/                # (optional)
│       └── __init__.py
│
├── widgets/                # (empty initially)
│
├── requirements.txt
└── package.json
```

## File Contents

### `server/main.py`

Complete server setup (copy this exactly):

```python
from pathlib import Path
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
                        print(f"[WARNING] Warning: No build result for '{tool_identifier}'")
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
    print(f"\n[START] Starting server with {len(tools)} tools")
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

**You don't need to modify this file.** It automatically discovers all widgets!

### `server/__init__.py`

```python
# Empty file
```

### `server/tools/__init__.py`

```python
# Empty file
```

### `requirements.txt`

```
fastapps>=1.0.3
httpx>=0.28.0
```

### `package.json`

```json
{
  "name": "my-chatgpt-widgets",
  "version": "1.0.0",
  "type": "module",
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
}
```

## Install Dependencies

```bash
# Python
pip install -r requirements.txt

# JavaScript
npm install
```

## Create Your First Widget

```bash
python -m fastapps.cli.main create greeting
```

This creates:

```
my-chatgpt-widgets/
├── server/
│   └── tools/
│       └── greeting_tool.py     # ← Generated with template
└── widgets/
    └── greeting/
        └── index.jsx            # ← Generated with template
```

## Build and Run

```bash
# Build widgets
npm run build

# Start server
python server/main.py
```

Done!

---

## Project Structure After Building

```
my-chatgpt-widgets/
├── server/
│   ├── __init__.py
│   ├── main.py                  # Auto-discovery server
│   └── tools/
│       ├── __init__.py
│       └── greeting_tool.py     # ← Your widget logic
│
├── widgets/
│   └── greeting/
│       └── index.jsx            # ← Your UI component
│
├── assets/                      # Auto-generated
│   ├── greeting-HASH.html
│   └── greeting-HASH.js
│
├── build-all.mts                # Auto-copied from chatjs-hooks
├── requirements.txt
└── package.json
```

**Key Points:**
- `server/main.py` - Already setup, no edits needed
- `assets/` - Auto-generated during build
- `build-all.mts` - Auto-copied from chatjs-hooks
- You only edit files in `server/tools/` and `widgets/`!

---

## Next Steps

1. [Tutorial: Build Your First Widget](./docs/TUTORIAL.md)
2. [API Reference](./docs/API.md)
3. [See Examples](../examples/)

