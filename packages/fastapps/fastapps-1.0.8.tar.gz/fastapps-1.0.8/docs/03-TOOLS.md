# Building Tools (Python Backend)

Learn how to create Python tools that power your ChatGPT widgets.

## What is a Tool?

A tool is a Python class that:
- Lives in `server/tools/<widget>_tool.py`
- Extends `BaseWidget`
- Defines inputs with Pydantic
- Implements widget logic in `execute()`

## Basic Tool Structure

```python
from fastapps import BaseWidget, Field, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

# 1. Define inputs
class MyWidgetInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str = Field(default="", description="User's name")

# 2. Create tool
class MyWidgetTool(BaseWidget):
    identifier = "mywidget"           # Must match widgets/mywidget/
    title = "My Widget"               # Display name
    input_schema = MyWidgetInput      # Input model
    invoking = "Loading..."           # Loading message
    invoked = "Ready!"                # Ready message
    
    widget_csp = {
        "connect_domains": [],        # External APIs
        "resource_domains": []        # External resources
    }
    
    # 3. Implement logic
    async def execute(self, input_data: MyWidgetInput) -> Dict[str, Any]:
        return {
            "message": f"Hello, {input_data.name}!"
        }
```

**That's the complete structure!**

## Defining Inputs

### Simple Fields

```python
from fastapps import Field, ConfigDict
from pydantic import BaseModel

class MyInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    # String
    name: str = Field(default="", description="User's name")
    
    # Number
    age: int = Field(default=0, description="User's age")
    
    # Boolean
    active: bool = Field(default=True, description="Is active")
    
    # List
    tags: list[str] = Field(default=[], description="Tags")
```

### Field Validation

```python
class MyInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    # Required field
    email: str = Field(..., description="Email (required)")
    
    # String pattern
    phone: str = Field(
        default="",
        pattern=r'^\d{3}-\d{3}-\d{4}$',
        description="Phone: 123-456-7890"
    )
    
    # Number range
    age: int = Field(default=0, ge=0, le=150, description="Age 0-150")
    
    # String length
    bio: str = Field(
        default="",
        min_length=10,
        max_length=500,
        description="Bio (10-500 chars)"
    )
```

### CamelCase to snake_case

```python
class MyInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    # ChatGPT sends "firstName", Python receives "first_name"
    first_name: str = Field(default="", alias="firstName")
    last_name: str = Field(default="", alias="lastName")
    phone_number: str = Field(default="", alias="phoneNumber")
```

### Complex Types

```python
from typing import List, Optional, Dict

class Address(BaseModel):
    street: str
    city: str
    zip_code: str

class MyInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    
    # Nested model
    address: Address = Field(default=None)
    
    # Optional
    middle_name: Optional[str] = Field(default=None)
    
    # List of models
    contacts: List[Address] = Field(default=[])
    
    # Dictionary
    metadata: Dict[str, str] = Field(default={})
```

## Implementing Logic

### Basic Execute

```python
async def execute(self, input_data: MyInput) -> Dict[str, Any]:
    # Your logic here
    result = process_data(input_data.name)
    
    return {
        "result": result,
        "timestamp": "2025-10-15"
    }
```

### With Error Handling

```python
async def execute(self, input_data: MyInput) -> Dict[str, Any]:
    try:
        result = await fetch_data(input_data.query)
        
        return {
            "success": True,
            "data": result
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch data"
        }
```

### With API Calls

```python
import httpx

async def execute(self, input_data: MyInput) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            params={"query": input_data.query},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": data
            }
        else:
            return {
                "success": False,
                "error": f"API returned {response.status_code}"
            }
```

### With Multiple API Calls

```python
import asyncio
import httpx

async def execute(self, input_data: MyInput) -> Dict[str, Any]:
    async with httpx.AsyncClient() as client:
        # Parallel requests
        weather_task = client.get("https://api.weather.com/data")
        news_task = client.get("https://api.news.com/headlines")
        
        weather_response, news_response = await asyncio.gather(
            weather_task,
            news_task
        )
        
        return {
            "weather": weather_response.json(),
            "news": news_response.json()
        }
```

### With Database

```python
import asyncpg  # or any async DB library

async def execute(self, input_data: MyInput) -> Dict[str, Any]:
    # Connect to database
    conn = await asyncpg.connect(
        user='user',
        password='password',
        database='mydb',
        host='localhost'
    )
    
    # Query
    rows = await conn.fetch(
        'SELECT * FROM users WHERE name = $1',
        input_data.name
    )
    
    await conn.close()
    
    return {
        "users": [dict(row) for row in rows]
    }
```

## Content Security Policy

### What is CSP?

CSP controls what external resources your widget can access.

### Connect Domains (APIs)

```python
widget_csp = {
    "connect_domains": [
        "https://api.openweathermap.org",
        "https://api.github.com",
        "https://newsapi.org"
    ],
    "resource_domains": []
}
```

**Use for:**
- API calls (fetch, axios, httpx)
- WebSocket connections
- Any network requests from React

### Resource Domains (Assets)

```python
widget_csp = {
    "connect_domains": [],
    "resource_domains": [
        "https://images.unsplash.com",
        "https://cdn.example.com",
        "https://fonts.googleapis.com"
    ]
}
```

**Use for:**
- Images (`<img src="...">`)
- Fonts (`@font-face`)
- Stylesheets (`<link>`)
- Scripts (rare)

### Example: Complete CSP

```python
widget_csp = {
    "connect_domains": [
        "https://api.openweathermap.org",    # API calls
        "https://geocoding.api.com"          # Geocoding
    ],
    "resource_domains": [
        "https://images.weather.com",        # Weather icons
        "https://cdn.weather.com"            # Assets
    ]
}
```

## Return Data

### Basic Return

```python
async def execute(self, input_data):
    return {
        "message": "Hello",
        "count": 42
    }
```

### Structured Data

```python
async def execute(self, input_data):
    return {
        "user": {
            "name": "John",
            "age": 30
        },
        "items": [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"}
        ],
        "metadata": {
            "timestamp": "2025-10-15",
            "version": "1.0"
        }
    }
```

### With Status

```python
async def execute(self, input_data):
    try:
        data = fetch_data()
        return {
            "success": True,
            "data": data,
            "message": "Data fetched successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to fetch data"
        }
```

## Common Patterns

### API Integration

```python
import httpx
from fastapps import BaseWidget

class APIWidget(BaseWidget):
    identifier = "api_widget"
    title = "API Widget"
    
    widget_csp = {
        "connect_domains": ["https://api.example.com"]
    }
    
    async def execute(self, input_data):
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.example.com/data",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                    timeout=10.0
                )
                response.raise_for_status()
                
                return {
                    "success": True,
                    "data": response.json()
                }
                
            except httpx.HTTPError as e:
                return {
                    "success": False,
                    "error": str(e)
                }
```

### Caching Results

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def expensive_computation(value: str) -> dict:
    # Expensive operation
    return result

class MyWidget(BaseWidget):
    async def execute(self, input_data):
        # Use cached result
        result = expensive_computation(input_data.query)
        return {"result": result}
```

### Rate Limiting

```python
import time
from collections import defaultdict

class RateLimitedWidget(BaseWidget):
    _requests = defaultdict(list)
    
    async def execute(self, input_data):
        # Simple rate limiting
        user_id = input_data.user_id
        now = time.time()
        
        # Remove old requests (older than 60 seconds)
        self._requests[user_id] = [
            t for t in self._requests[user_id]
            if now - t < 60
        ]
        
        # Check limit (max 10 requests per minute)
        if len(self._requests[user_id]) >= 10:
            return {
                "error": "Rate limit exceeded",
                "retry_after": 60
            }
        
        # Add this request
        self._requests[user_id].append(now)
        
        # Process normally
        return {"result": "..."}
```

## Testing Tools

### Unit Testing

```python
import pytest
from server.tools.mywidget_tool import MyWidgetTool, MyWidgetInput

@pytest.mark.asyncio
async def test_mywidget_basic():
    # Create tool instance
    tool = MyWidgetTool(build_result)
    
    # Create input
    input_data = MyWidgetInput(name="Test")
    
    # Execute
    result = await tool.execute(input_data)
    
    # Assert
    assert result["success"] == True
    assert "data" in result
```

### Mocking APIs

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_api_call(mock_get):
    # Mock response
    mock_response = AsyncMock()
    mock_response.json.return_value = {"temp": 72}
    mock_get.return_value = mock_response
    
    # Test
    tool = WeatherTool(build_result)
    result = await tool.execute(WeatherInput(city="NYC"))
    
    assert result["temperature"] == 72
```

## Best Practices

1. **Always handle errors** - Never let exceptions bubble up
2. **Use type hints** - Helps with IDE support and debugging
3. **Validate inputs** - Use Pydantic constraints
4. **Keep execute() simple** - Extract complex logic to helper functions
5. **Use async/await** - For I/O operations
6. **Log appropriately** - Use print() for important events
7. **Document CSP** - Comment why each domain is needed
8. **Test edge cases** - Empty inputs, API failures, timeouts

## Common Issues

### Identifier Mismatch

```python
# Wrong
class MyTool(BaseWidget):
    identifier = "my_tool"    # But folder is widgets/mywidget/

# Correct
class MyTool(BaseWidget):
    identifier = "mywidget"   # Matches widgets/mywidget/
```

### Missing CSP

```python
# API call without CSP
async def execute(self, input_data):
    response = await client.get("https://api.example.com")
    # Will fail! CSP blocks it

# With proper CSP
widget_csp = {
    "connect_domains": ["https://api.example.com"]
}
```

### Synchronous Code

```python
# Blocking synchronous code
def execute(self, input_data):  # Should be async!
    result = requests.get("...")  # Blocks event loop
    return {"data": result.json()}

# Async code
async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        response = await client.get("...")
        return {"data": response.json()}
```

## Next Steps

- [Managing State](./04-STATE.md) - Widget state persistence
- [API Integration](./06-API.md) - Working with external APIs
- [Security](./07-SECURITY.md) - CSP and security best practices
- [Examples](../examples/) - Real-world tools

