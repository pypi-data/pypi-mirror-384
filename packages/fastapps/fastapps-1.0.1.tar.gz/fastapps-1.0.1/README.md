# FastApps Framework

<p align="center">
  <strong>A zero-boilerplate framework for building interactive ChatGPT widgets</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/fastapps/"><img src="https://img.shields.io/pypi/v/fastapps.svg" alt="PyPI"></a>
  <a href="https://pypi.org/project/fastapps/"><img src="https://img.shields.io/pypi/pyversions/fastapps.svg" alt="Python"></a>
  <a href="https://github.com/fastapps-framework/fastapps/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
</p>

---

## 🚀 Quick Start

### 1. Create Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate    # macOS/Linux
venv\Scripts\activate       # Windows
```

### 2. Install FastApps & Create Project

```bash
pip install fastapps
fastapps init my-widgets
```

This generates the complete project structure:

```
my-widgets/
├── server/
│   ├── __init__.py
│   ├── main.py              # Auto-discovery server
│   ├── tools/               # Widget backends
│   │   └── __init__.py
│   └── api/                 # (optional) Shared APIs
│       └── __init__.py
├── widgets/                 # Widget frontends (empty initially)
├── requirements.txt         # Python dependencies
├── package.json             # JavaScript dependencies
├── .gitignore
└── README.md
```

### 3. Install Dependencies

```bash
cd my-widgets
pip install -r requirements.txt
npm install
```

### 4. Create Your First Widget

```bash
fastapps create greeting
```

This adds to your project:

```
my-widgets/
├── server/
│   └── tools/
│       └── greeting_tool.py # ← Generated: Widget backend
└── widgets/
    └── greeting/
        └── index.jsx        # ← Generated: Widget frontend
```

### 5. Edit Your Widget Code

**You only need to edit these 2 files:**

#### `server/tools/greeting_tool.py` - Backend Logic

```python
from fastapps import BaseWidget, Field, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

class GreetingInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(default="World")

class GreetingTool(BaseWidget):
    identifier = "greeting"
    title = "Greeting Widget"
    input_schema = GreetingInput
    invoking = "Preparing greeting..."
    invoked = "Greeting ready!"
    
    widget_csp = {
        "connect_domains": [],      # APIs you'll call
        "resource_domains": []      # Images/fonts you'll use
    }
    
    async def execute(self, input_data: GreetingInput) -> Dict[str, Any]:
        # Your logic here
        return {
            "name": input_data.name,
            "message": f"Hello, {input_data.name}!"
        }
```

#### `widgets/greeting/index.jsx` - Frontend UI

```jsx
import React from 'react';
import { useWidgetProps } from 'chatjs-hooks';

export default function Greeting() {
  const props = useWidgetProps();
  
  return (
    <div style={{
      padding: '40px',
      textAlign: 'center',
      background: '#4A90E2',
      color: 'white',
      borderRadius: '12px'
    }}>
      <h1>👋 {props.message}</h1>
      <p>Welcome, {props.name}!</p>
    </div>
  );
}
```

**That's it! These are the only files you need to write.**

### 6. Build and Run

```bash
# Build
npm run build

# Start server
python server/main.py
```

Your widget is now live at `http://localhost:8001` 🎉

---

## 📦 What You Need to Know

### Widget Structure

Every widget has **exactly 2 files you write**:

1. **Python Tool** (`server/tools/*_tool.py`)
   - Define inputs with Pydantic
   - Write your logic in `execute()`
   - Return data as a dictionary

2. **React Component** (`widgets/*/index.jsx`)
   - Get data with `useWidgetProps()`
   - Render your UI
   - Use inline styles

**Everything else is automatic:**
- ✅ Widget discovery
- ✅ Registration
- ✅ Build process
- ✅ Server setup
- ✅ Mounting logic

### Input Schema

```python
from fastapps import Field, ConfigDict
from pydantic import BaseModel

class MyInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    name: str = Field(default="", description="User's name")
    age: int = Field(default=0, ge=0, le=150)
    email: str = Field(default="", pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
```

### CSP (Content Security Policy)

Allow external resources:

```python
widget_csp = {
    "connect_domains": ["https://api.example.com"],     # For API calls
    "resource_domains": ["https://cdn.example.com"]     # For images/fonts
}
```

### React Hooks

```jsx
import { useWidgetProps, useWidgetState, useOpenAiGlobal } from 'chatjs-hooks';

function MyWidget() {
  const props = useWidgetProps();              // Data from Python
  const [state, setState] = useWidgetState({}); // Persistent state
  const theme = useOpenAiGlobal('theme');      // ChatGPT theme
  
  return <div>{props.message}</div>;
}
```

---

## 📚 Documentation

- **[Quick Start Guide](./docs/QUICKSTART.md)** - Detailed setup instructions
- **[Tutorial](./docs/TUTORIAL.md)** - Step-by-step widget examples
- **[API Reference](./docs/API.md)** - Complete API documentation
- **[Examples](../examples/)** - Real-world widget examples

---

## 🔧 CLI Commands

```bash
# Create new widget (auto-generates both files)
python -m fastapps.cli.main create mywidget

# Or if installed globally:
fastapps create mywidget
```

---

## 📖 Project Structure After `fastapps create`

When you run `python -m fastapps.cli.main create greeting`, you get:

```
my-widgets/
├── server/
│   ├── __init__.py
│   ├── main.py                  # ✅ Already setup (no edits needed)
│   ├── tools/
│   │   ├── __init__.py
│   │   └── greeting_tool.py     # ← Edit this: Your widget logic
│   └── api/                     # (optional: for shared APIs)
│
├── widgets/
│   └── greeting/
│       └── index.jsx            # ← Edit this: Your UI
│
├── assets/                      # ⚙️ Auto-generated during build
│   ├── greeting-HASH.html
│   └── greeting-HASH.js
│
├── requirements.txt             # Python dependencies
├── package.json                 # JavaScript dependencies
└── build-all.mts                # ⚙️ Auto-copied from chatjs-hooks
```

**You only edit the 2 files marked with ←**

---

## 🎯 Key Features

- ✅ **Zero Boilerplate** - Just write your widget code
- ✅ **Auto-Discovery** - Widgets automatically registered
- ✅ **Type-Safe** - Pydantic for Python, TypeScript for React
- ✅ **CLI Tools** - Scaffold widgets instantly
- ✅ **React Hooks** - Modern React patterns via `chatjs-hooks`
- ✅ **MCP Protocol** - Native ChatGPT integration

---

## 💡 Examples

### Simple Widget

```python
# server/tools/hello_tool.py
class HelloTool(BaseWidget):
    identifier = "hello"
    title = "Hello"
    input_schema = HelloInput
    
    async def execute(self, input_data):
        return {"message": "Hello World!"}
```

```jsx
// widgets/hello/index.jsx
export default function Hello() {
  const props = useWidgetProps();
  return <h1>{props.message}</h1>;
}
```

### With API Call

```python
async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        data = response.json()
    return {"data": data}
```

### With State

```jsx
function Counter() {
  const [state, setState] = useWidgetState({ count: 0 });
  return (
    <button onClick={() => setState({ count: state.count + 1 })}>
      Count: {state.count}
    </button>
  );
}
```

---

## 🐛 Troubleshooting

**Widget not loading?**
- Check `identifier` matches folder name
- Rebuild: `npm run build`
- Restart: `python server/main.py`

**Import errors?**
```bash
pip install --upgrade fastapps
npm install chatjs-hooks@latest
```

**Need help?** Check our [docs](./docs/) or [open an issue](https://github.com/fastapps-framework/fastapps/issues)

---

## 🤝 Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md)

## 📄 License

MIT © FastApps Team

## 🔗 Links

- **PyPI**: https://pypi.org/project/fastapps/
- **ChatJS Hooks**: https://www.npmjs.com/package/chatjs-hooks
- **GitHub**: https://github.com/fastapps-framework/fastapps
- **MCP Spec**: https://modelcontextprotocol.io/
