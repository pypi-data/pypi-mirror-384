# Introduction to Floydr

Welcome to Floydr - a zero-boilerplate framework for building interactive ChatGPT widgets!

## What is Floydr?

Floydr is a Python framework that lets you build interactive, visual widgets for ChatGPT with minimal code. Instead of text-only responses, you can create rich, interactive UIs that run directly in ChatGPT.

## Why Floydr?

### Traditional ChatGPT Development
```python
# Just text responses
def my_tool():
    return "Here's the weather: 72°F, Sunny"
```

### With Floydr
```python
# Rich, interactive widgets
class WeatherWidget(BaseWidget):
    async def execute(self, input_data):
        return {
            "temperature": 72,
            "condition": "Sunny",
            "forecast": [...]
        }
```

```jsx
// Beautiful UI
<div style={{ background: 'linear-gradient(...)' }}>
  <h1>🌤️ {temperature}°F</h1>
  <p>{condition}</p>
  {/* Interactive charts, maps, etc */}
</div>
```

## Key Features

### 🚀 Zero Boilerplate
- No configuration files needed
- No manual registration
- No build configuration
- Just write your widget code!

### 🔄 Auto-Discovery
```python
# Drop a file in server/tools/
class MyWidget(BaseWidget):
    identifier = "mywidget"
    # ...

# It's automatically registered! No imports needed.
```

### ⚡ Fast Development
```bash
floydr create mywidget  # Generate files
# Edit 2 files
npm run build           # Build
python server/main.py   # Run
```

### 🎨 Modern Stack
- **Backend**: Python + FastMCP
- **Frontend**: React + Vite
- **Protocol**: MCP (Model Context Protocol)
- **Type Safety**: Pydantic + TypeScript

## Architecture Overview

```
┌─────────────────────────────────────────┐
│           ChatGPT Interface             │
└─────────────────┬───────────────────────┘
                  │ MCP Protocol
                  ▼
┌─────────────────────────────────────────┐
│         Floydr Framework                │
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

## Comparison

| Feature | Traditional ChatGPT | Floydr Widgets |
|---------|-------------------|----------------|
| **Output** | Text only | Rich UI |
| **Interactivity** | Limited | Full React |
| **Visualization** | ASCII art | Charts, maps, images |
| **State** | Conversation only | Persistent widget state |
| **Styling** | None | Full CSS/styling |

## How It Works

1. **You write**: Python tool + React component
2. **Floydr discovers**: Automatically finds your widget
3. **Floydr builds**: Bundles with Vite
4. **Floydr serves**: MCP server handles requests
5. **ChatGPT renders**: Your widget appears in chat

## Design Philosophy

### Minimal API Surface
- 1 base class: `BaseWidget`
- 3 React hooks: `useWidgetProps`, `useWidgetState`, `useOpenAiGlobal`
- 2 CLI commands: `init`, `create`

### Convention Over Configuration
- Identifier must match folder name
- Tools in `server/tools/`, components in `widgets/`
- No config files needed

### Developer Experience First
- Hot reload in development
- Clear error messages
- TypeScript support
- Comprehensive docs

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

> "You should only write the code that's unique to your widget. Everything else should be automatic."

That's Floydr. 🚀

