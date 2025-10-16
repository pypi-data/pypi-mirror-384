# Introduction to FastApps

Welcome to FastApps - a zero-boilerplate framework for building interactive ChatGPT widgets powered by the Apps SDK!

## What is FastApps?

FastApps is a Python framework that eliminates the complexity of building Apps SDK widgets for ChatGPT. It handles all the MCP protocol boilerplate, auto-discovery, and build configuration so you can focus on writing your widget logic and UI.

## The Problem: MCP is Powerful but Complex

OpenAI's Apps SDK lets you build rich, interactive widgets for ChatGPT using the Model Context Protocol (MCP). But the manual setup is extensive:

### Building a Widget with Raw MCP
```typescript
// 1. Manually register HTML resources with specific mime types
server.registerResource(
  "widget-html",
  "ui://widget/my-widget.html",
  {},
  async () => ({
    contents: [{
      uri: "ui://widget/my-widget.html",
      mimeType: "text/html+skybridge",  // Must be exact
      text: `
        <div id="root"></div>
        <style>${CSS}</style>
        <script type="module">${JS}</script>
      `,
      _meta: {
        "openai/widgetCSP": {
          connect_domains: [],
          resource_domains: []
        }
      }
    }]
  })
);

// 2. Manually wire tool metadata to resource URIs
server.registerTool(
  "my-widget",
  {
    title: "My Widget",
    inputSchema: { /* ... */ },
    _meta: {
      "openai/outputTemplate": "ui://widget/my-widget.html",
      "openai/widgetAccessible": true,
      "openai/toolInvocation/invoking": "Loading...",
      "openai/toolInvocation/invoked": "Done"
    }
  },
  async (input) => {
    return {
      content: [{ type: "text", text: "Success" }],
      structuredContent: { /* data */ }
    };
  }
);

// 3. Manually build and bundle assets
// 4. Manually inject component mounting logic
// 5. Manually configure CSP policies
// 6. Manually set up server with proper protocol handlers
```

**That's a lot of boilerplate for every widget you build.**

## The Solution: FastApps Automates Everything

With FastApps, you write **just 2 files** and everything else is automatic:

### Python Tool (Backend)
```python
from fastapps import BaseWidget, Field
from pydantic import BaseModel

class MyInput(BaseModel):
    name: str = Field(default="World")

class MyWidgetTool(BaseWidget):
    identifier = "my-widget"
    title = "My Widget"
    input_schema = MyInput
    invoking = "Loading..."
    invoked = "Done"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: MyInput):
        return {
            "message": f"Hello, {input_data.name}!"
        }
```

### React Component (Frontend)
```jsx
import React from 'react';
import { useWidgetProps } from 'chatjs-hooks';

export default function MyWidget() {
  const props = useWidgetProps();
  
  return (
    <div style={{
      padding: '40px',
      textAlign: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      color: 'white',
      borderRadius: '12px'
    }}>
      <h1>{props.message}</h1>
    </div>
  );
}
```

**That's it! FastApps handles:**
- ✅ MCP server setup and protocol implementation
- ✅ Tool and resource registration
- ✅ HTML resource generation with proper mime types
- ✅ Metadata wiring (`openai/outputTemplate`, CSP, etc.)
- ✅ Asset building and bundling with Vite
- ✅ Component mounting logic injection
- ✅ Auto-discovery of widgets from your project structure

## Key Features

### Zero Boilerplate
No more manual MCP server setup:
- ✅ **No resource registration** - FastApps auto-generates HTML resources
- ✅ **No metadata wiring** - Tool metadata automatically configured
- ✅ **No build scripts** - Vite integration built-in
- ✅ **No mounting logic** - Component initialization injected automatically

### Auto-Discovery
Drop a Python file in `server/tools/` and it's automatically discovered:

```python
# server/tools/my_widget_tool.py
class MyWidgetTool(BaseWidget):
    identifier = "my-widget"
    # ...

# That's it! No imports, no manual registration needed.
```

FastApps scans your `server/tools/` directory, finds all `BaseWidget` subclasses, and automatically:
- Registers them as MCP tools
- Creates HTML resources with correct mime types
- Wires metadata (`openai/outputTemplate`, CSP, etc.)
- Links them to your React components in `widgets/`

### Fast Development Workflow
```bash
fastapps create mywidget  # Generate boilerplate (2 files)
# Edit server/tools/mywidget_tool.py (your logic)
# Edit widgets/mywidget/index.jsx (your UI)
npm run build             # Build assets
python server/main.py     # Run MCP server
```

That's it! No configuration files, no manual wiring.

### Modern Stack
- **Backend**: Python + FastMCP (MCP protocol wrapper)
- **Frontend**: React + Vite (fast builds)
- **Protocol**: MCP (Model Context Protocol)
- **Type Safety**: Pydantic (Python) + TypeScript (React)
- **CLI**: Scaffolding commands for instant widget creation

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           ChatGPT Interface             │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol
                  ▼
┌─────────────────────────────────────────┐
│         FastApps Framework                │
├─────────────────────────────────────────┤
│  Python Backend (Your Tool)             │
│  ├── Input validation (Pydantic)        │
│  ├── Business logic                     │
│  └── Data preparation                   │
└─────────────────┬───────────────────────┘
                  │ Props
                  ▼
┌─────────────────────────────────────────┐
│  React Frontend (Your Component)        │
│  ├── useWidgetProps() - Get data        │
│  ├── useWidgetState() - Manage state    │
│  └── Render UI                          │
└─────────────────────────────────────────┘
```

## Core Concepts

### 1. Widget = Tool + Component

Every widget consists of:
- **Tool** (Python): Backend logic, data fetching
- **Component** (React): UI rendering, interactivity

### 2. Automatic Everything

- **Discovery**: Tools automatically found in `server/tools/`
- **Registration**: No manual imports needed
- **Building**: Vite builds and bundles automatically
- **Mounting**: React mounting injected automatically

### 3. Type Safety

```python
# Python: Pydantic models
class MyInput(BaseModel):
    name: str
    age: int
```

```typescript
// TypeScript: Full type support
interface MyProps {
  name: string;
  age: number;
}
const props = useWidgetProps<MyProps>();
```

## What Can You Build?

### Data Visualizations
- Charts and graphs
- Maps and geospatial data
- Tables and grids
- Dashboards

### Interactive Tools
- Calculators
- Converters
- Form builders
- Quiz apps

### Content Displays
- Image galleries
- Video players
- Rich text editors
- Code highlighters

### Integrations
- API data displays
- Database queries
- External service UIs
- Real-time updates

## Comparison: Raw MCP vs FastApps

| Aspect | Raw MCP (Apps SDK) | FastApps |
|--------|-------------------|----------|
| **Setup** | Manual server config, protocol handlers | Auto-configured |
| **Resource Registration** | Manual `registerResource()` calls | Auto-generated |
| **Tool Registration** | Manual `registerTool()` with metadata | Auto-discovered |
| **CSP Configuration** | Manual `_meta` object wiring | Simple `widget_csp` dict |
| **Asset Bundling** | Custom build scripts | Built-in Vite integration |
| **Component Mounting** | Manual injection logic | Auto-injected |
| **Files to Write** | 5+ (server, resource, tool, build, component) | **2** (tool.py, index.jsx) |
| **Lines of Boilerplate** | ~150+ per widget | **~0** |

## How It Works (Under the Hood)

When you run `python server/main.py`, FastApps:

1. **Scans `server/tools/`** - Discovers all `BaseWidget` subclasses
2. **Auto-registers resources** - Creates HTML resources with `text/html+skybridge` mime type
3. **Auto-registers tools** - Wires tool metadata to resource URIs
4. **Configures CSP** - Converts your `widget_csp` dict to proper MCP metadata
5. **Serves MCP protocol** - Handles all protocol handshakes and requests
6. **Injects data** - Passes your `execute()` return value to React via `window.openai.toolOutput`

All the MCP complexity is handled for you - you just write business logic and UI.

## Design Philosophy

### Abstraction Without Leakage
FastApps hides MCP complexity but doesn't limit what you can build:
- All Apps SDK features supported (CSP, state, tool access)
- You control the data and UI completely
- MCP protocol details abstracted away

### Minimal API Surface
Learn once, build many:
- **1 base class**: `BaseWidget` (handles all MCP wiring)
- **3 React hooks**: `useWidgetProps`, `useWidgetState`, `useOpenAiGlobal`
- **2 CLI commands**: `init` (scaffold project), `create` (add widget)

### Convention Over Configuration
Zero config files:
- Widget identifier must match folder name (enforced automatically)
- Tools in `server/tools/`, components in `widgets/` (auto-discovered)
- Build and serve with standard commands

### Developer Experience First
- **Fast iterations** - Edit code, rebuild, reload
- **Clear errors** - Helpful validation messages
- **Type safety** - Pydantic + TypeScript
- **No surprises** - Explicit over implicit

## Next Steps

- [Quick Start Guide](./QUICKSTART.md) - Get started in 5 minutes
- [Building Widgets](./02-WIDGETS.md) - Create React components
- [Building Tools](./03-TOOLS.md) - Create Python backends
- [Managing State](./04-STATE.md) - Persistent widget state
- [API Reference](./API.md) - Complete API docs

## Requirements

- Python 3.11+
- Node.js 18+
- pip and npm

## Philosophy

> **"You should write your widget logic and UI, not MCP boilerplate."**

FastApps is an abstraction layer over the Apps SDK. It handles all the protocol complexity so you can focus on building great widgets.

---

**Ready to get started?** → [Quick Start Guide](./QUICKSTART.md)

