# FastApps API Reference

Complete API documentation for the FastApps framework.

## Core Classes

### BaseWidget

The base class for all FastApps widgets.

```python
from fastapps import BaseWidget
```

#### Class Attributes

**`identifier: str`** (required)
- Unique widget identifier
- Must match the widget folder name in `widgets/`
- Example: `"greeting"` for `widgets/greeting/`

**`title: str`** (required)
- Human-readable widget name
- Displayed in ChatGPT interface
- Example: `"Greeting Widget"`

**`input_schema: Type[BaseModel]`** (required)
- Pydantic model defining widget inputs
- Example: `GreetingInput`

**`invoking: str`** (required)
- Message shown while widget is loading
- Example: `"Preparing widget..."`

**`invoked: str`** (required)
- Message shown when widget is ready
- Example: `"Widget ready!"`

**`widget_csp: dict`** (required)
- Content Security Policy configuration
- Format:
  ```python
  {
      "connect_domains": ["https://api.example.com"],
      "resource_domains": ["https://cdn.example.com"]
  }
  ```

#### Methods

**`async execute(input_data: InputSchema) -> Dict[str, Any]`** (required)
- Main widget logic
- Parameters:
  - `input_data`: Instance of your input schema
- Returns: Dictionary of data to pass to React component
- Example:
  ```python
  async def execute(self, input_data: MyInput) -> Dict[str, Any]:
      return {
          "message": "Hello",
          "count": 42
      }
  ```

#### Example

```python
from fastapps import BaseWidget, Field, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

class MyWidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(default="")

class MyWidgetTool(BaseWidget):
    identifier = "mywidget"
    title = "My Widget"
    input_schema = MyWidgetInput
    invoking = "Loading..."
    invoked = "Ready!"
    
    widget_csp = {
        "connect_domains": [],
        "resource_domains": []
    }
    
    async def execute(self, input_data: MyWidgetInput) -> Dict[str, Any]:
        return {"name": input_data.name}
```

---

### WidgetBuilder

Builds all widgets in the project.

```python
from fastapps import WidgetBuilder
```

#### Constructor

```python
WidgetBuilder(project_root: Path | str)
```

**Parameters:**
- `project_root`: Path to project root directory

**Example:**
```python
from pathlib import Path
builder = WidgetBuilder(Path(__file__).parent.parent)
```

#### Methods

**`build_all() -> Dict[str, WidgetBuildResult]`**
- Builds all widgets in `widgets/` directory
- Returns: Dictionary mapping widget identifiers to build results
- Example:
  ```python
  build_results = builder.build_all()
  # build_results = {
  #     "greeting": WidgetBuildResult(...),
  #     "weather": WidgetBuildResult(...)
  # }
  ```

---

### WidgetMCPServer

MCP server for serving widgets.

```python
from fastapps import WidgetMCPServer
```

#### Constructor

```python
WidgetMCPServer(name: str, widgets: List[BaseWidget])
```

**Parameters:**
- `name`: Server name (appears in logs)
- `widgets`: List of widget instances

**Example:**
```python
server = WidgetMCPServer(
    name="my-widgets",
    widgets=[greeting_widget, weather_widget]
)
```

#### Methods

**`get_app() -> FastAPI`**
- Returns FastAPI application instance
- Used with uvicorn to start server
- Example:
  ```python
  app = server.get_app()
  uvicorn.run(app, host="0.0.0.0", port=8001)
  ```

---

## Input Schema

### Field

Pydantic Field for defining widget inputs.

```python
from fastapps import Field
```

**Common Parameters:**
- `default`: Default value
- `description`: Human-readable description
- `alias`: Alternative name (for camelCase/snake_case conversion)
- `ge`, `le`: Greater/less than or equal (for numbers)
- `min_length`, `max_length`: String length constraints
- `pattern`: Regex pattern for validation

**Examples:**

```python
from fastapps import Field
from pydantic import BaseModel

class MyInput(BaseModel):
    # Simple field
    name: str = Field(default="")
    
    # With description
    age: int = Field(default=0, description="User's age")
    
    # With alias (camelCase in ChatGPT, snake_case in Python)
    user_name: str = Field(default="", alias="userName")
    
    # With validation
    email: str = Field(
        default="",
        pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$',
        description="Valid email address"
    )
    
    # Number constraints
    score: int = Field(default=0, ge=0, le=100)
    
    # String length
    bio: str = Field(default="", max_length=500)
```

### ConfigDict

Pydantic configuration.

```python
from fastapps import ConfigDict
from pydantic import BaseModel

class MyInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    # Always include this for proper field alias handling
```

---

## React Hooks (fastapps)

### useWidgetProps

Access data from Python backend.

```typescript
function useWidgetProps<T = any>(): T
```

**Returns:** Data returned from `BaseWidget.execute()`

**Example:**
```jsx
import { useWidgetProps } from 'fastapps';

function MyWidget() {
  const props = useWidgetProps();
  // props contains data from execute()
  
  return <div>{props.message}</div>;
}
```

**With TypeScript:**
```typescript
interface MyProps {
  message: string;
  count: number;
}

function MyWidget() {
  const props = useWidgetProps<MyProps>();
  return <div>{props.message}</div>;
}
```

---

### useWidgetState

Manage persistent widget state.

```typescript
function useWidgetState<T>(
  initialState: T
): [T, (newState: T) => void]
```

**Parameters:**
- `initialState`: Initial state value

**Returns:** `[state, setState]` tuple

**Example:**
```jsx
import { useWidgetState } from 'fastapps';

function Counter() {
  const [state, setState] = useWidgetState({ count: 0 });
  
  const increment = () => {
    setState({ count: state.count + 1 });
  };
  
  return (
    <div>
      <p>Count: {state.count}</p>
      <button onClick={increment}>+</button>
    </div>
  );
}
```

---

### useOpenAiGlobal

Access ChatGPT global values and environment information.

```typescript
function useOpenAiGlobal<K extends keyof OpenAiGlobals>(
  key: K
): OpenAiGlobals[K] | null
```

**Parameters:**
- `key`: Global property name (see available keys below)

**Available Keys:**

| Key | Type | Description | Example |
|-----|------|-------------|---------|
| `theme` | `'light' \| 'dark'` | ChatGPT's current theme | `'dark'` |
| `displayMode` | `'inline' \| 'pip' \| 'fullscreen'` | Current display mode | `'inline'` |
| `locale` | `string` | User's preferred locale (IETF BCP 47) | `'en-US'`, `'fr-FR'` |
| `maxHeight` | `number` | Maximum height constraint in pixels | `600` |
| `safeArea` | `SafeArea` | Safe area insets for mobile | `{ insets: { top: 20, ... }}` |
| `userAgent` | `UserAgent` | Device and capability info | `{ device: { type: 'mobile' }}` |
| `toolInput` | `object` | Input parameters | `{ city: 'NYC' }` |
| `toolOutput` | `object` | Tool output (same as `useWidgetProps()`) | `{ message: 'Hello' }` |
| `widgetState` | `object` | Persistent state (same as `useWidgetState()`) | `{ count: 5 }` |

**Example:**
```jsx
import { useOpenAiGlobal } from 'fastapps';

function ThemedWidget() {
  const theme = useOpenAiGlobal('theme');
  const displayMode = useOpenAiGlobal('displayMode');
  const maxHeight = useOpenAiGlobal('maxHeight');
  const userAgent = useOpenAiGlobal('userAgent');
  
  return (
    <div style={{
      background: theme === 'dark' ? '#1a1a1a' : '#ffffff',
      color: theme === 'dark' ? '#ffffff' : '#000000',
      maxHeight: `${maxHeight}px`,
      padding: userAgent?.device.type === 'mobile' ? '8px' : '16px'
    }}>
      <p>Theme: {theme}</p>
      <p>Mode: {displayMode}</p>
    </div>
  );
}
```

---

## window.openai API

For advanced use cases, access the raw `window.openai` API directly:

### callTool

Call an MCP tool from your component.

```typescript
window.openai.callTool(
  name: string,
  args: Record<string, unknown>
): Promise<CallToolResponse>
```

**Requirements:**
- Set `widget_accessible = True` in your Python tool

**Example:**
```jsx
const handleRefresh = async () => {
  await window.openai.callTool('refresh_data', {
    city: 'New York'
  });
};
```

---

### sendFollowUpMessage

Inject a message into the ChatGPT conversation.

```typescript
window.openai.sendFollowUpMessage(args: {
  prompt: string
}): Promise<void>
```

**Example:**
```jsx
const askMore = async () => {
  await window.openai.sendFollowUpMessage({
    prompt: 'Tell me more about this topic'
  });
};
```

---

### requestDisplayMode

Request a display mode change (inline, PiP, fullscreen).

```typescript
window.openai.requestDisplayMode(args: {
  mode: 'inline' | 'pip' | 'fullscreen'
}): Promise<{ mode: DisplayMode }>
```

**Notes:**
- Host may reject or coerce the request
- On mobile, PiP is always coerced to fullscreen

**Example:**
```jsx
const goFullscreen = async () => {
  const result = await window.openai.requestDisplayMode({
    mode: 'fullscreen'
  });
  console.log('Granted mode:', result.mode);
};
```

---

### openExternal

Open an external URL in a new window.

```typescript
window.openai.openExternal(payload: {
  href: string
}): void
```

**Example:**
```jsx
const openLink = (url: string) => {
  window.openai.openExternal({ href: url });
};
```

---

### setWidgetState

Update persistent widget state (also available via `useWidgetState`).

```typescript
window.openai.setWidgetState(
  state: Record<string, unknown>
): Promise<void>
```

**Example:**
```jsx
await window.openai.setWidgetState({
  favorites: ['item1', 'item2']
});
```

---

## TypeScript Types (fastapps)

```typescript
import type {
  OpenAiGlobals,
  Theme,
  DisplayMode,
  UserAgent,
  SafeArea,
  SafeAreaInsets,
  DeviceType,
  CallToolResponse
} from 'fastapps';

// Theme
type Theme = 'light' | 'dark';

// Display mode
type DisplayMode = 'pip' | 'inline' | 'fullscreen';

// Device type
type DeviceType = 'mobile' | 'tablet' | 'desktop' | 'unknown';

// User agent
type UserAgent = {
  device: { type: DeviceType };
  capabilities: {
    hover: boolean;
    touch: boolean;
  };
};

// Safe area
type SafeAreaInsets = {
  top: number;
  bottom: number;
  left: number;
  right: number;
};

type SafeArea = {
  insets: SafeAreaInsets;
};

// OpenAI Globals
type OpenAiGlobals<
  ToolInput = any,
  ToolOutput = any,
  ToolResponseMetadata = any,
  WidgetState = any
> = {
  theme: Theme;
  userAgent: UserAgent;
  locale: string;
  maxHeight: number;
  displayMode: DisplayMode;
  safeArea: SafeArea;
  toolInput: ToolInput;
  toolOutput: ToolOutput | null;
  toolResponseMetadata: ToolResponseMetadata | null;
  widgetState: WidgetState | null;
  setWidgetState: (state: WidgetState) => Promise<void>;
};
```

---

## CLI Commands

### Create Widget

```bash
python -m fastapps.cli.main create WIDGET_NAME
```

**Creates:**
- `server/tools/WIDGET_NAME_tool.py`
- `widgets/WIDGET_NAME/index.jsx`

**Example:**
```bash
python -m fastapps.cli.main create weather
```

### Version

```bash
python -m fastapps.cli.main --version
```

---

## Content Security Policy

### Structure

```python
widget_csp = {
    "connect_domains": [...],    # For fetch/API calls
    "resource_domains": [...]    # For images, fonts, etc
}
```

### Examples

**API Access:**
```python
widget_csp = {
    "connect_domains": [
        "https://api.openweathermap.org",
        "https://api.github.com"
    ],
    "resource_domains": []
}
```

**Image Resources:**
```python
widget_csp = {
    "connect_domains": [],
    "resource_domains": [
        "https://images.unsplash.com",
        "https://cdn.example.com"
    ]
}
```

**Both:**
```python
widget_csp = {
    "connect_domains": ["https://api.example.com"],
    "resource_domains": ["https://cdn.example.com"]
}
```

---

## Type Definitions

### WidgetBuildResult

```python
class WidgetBuildResult:
    html_path: str      # Path to built HTML
    js_path: str        # Path to built JS
    hash: str           # Build hash
```

---

## Error Handling

### Python Exceptions

```python
class WidgetError(Exception):
    """Base exception for widget errors"""
    pass

class BuildError(WidgetError):
    """Raised when widget build fails"""
    pass
```

### Handling Errors

```python
async def execute(self, input_data):
    try:
        # Your logic
        result = await some_async_operation()
        return {"success": True, "data": result}
    except Exception as e:
        # Return error to React component
        return {
            "success": False,
            "error": str(e),
            "message": "Something went wrong"
        }
```

---

## Best Practices

1. **Always handle errors** in `execute()` method
2. **Use type hints** for better IDE support
3. **Validate inputs** with Pydantic constraints
4. **Keep widgets simple** - one responsibility per widget
5. **Use descriptive identifiers** and titles
6. **Document your inputs** with Field descriptions
7. **Test with different themes** using `useOpenAiGlobal`
8. **Handle loading states** in React components

---

## Next Steps

- [Tutorial](./TUTORIAL.md)
- [Advanced Features](./ADVANCED.md)
- [Examples](../../examples/)

