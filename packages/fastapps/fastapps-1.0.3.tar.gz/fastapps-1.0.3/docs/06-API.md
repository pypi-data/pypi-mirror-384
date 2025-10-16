# API Integration

Learn how to integrate external APIs into your FastApps widgets.

## Overview

API integration happens in two places:
1. **Python Tool** - Makes the API call, processes data
2. **React Component** - Displays the data

## Basic API Call

### Python Tool

```python
import httpx
from fastapps import BaseWidget, Field, ConfigDict
from pydantic import BaseModel
from typing import Dict, Any

class WeatherInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    city: str = Field(..., description="City name")

class WeatherTool(BaseWidget):
    identifier = "weather"
    title = "Weather Widget"
    input_schema = WeatherInput
    invoking = "Fetching weather..."
    invoked = "Weather ready!"
    
    # IMPORTANT: Add API domain to CSP
    widget_csp = {
        "connect_domains": ["https://api.openweathermap.org"],
        "resource_domains": []
    }
    
    async def execute(self, input_data: WeatherInput) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "https://api.openweathermap.org/data/2.5/weather",
                    params={
                        "q": input_data.city,
                        "appid": "YOUR_API_KEY",
                        "units": "metric"
                    },
                    timeout=10.0
                )
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "temperature": data["main"]["temp"],
                    "condition": data["weather"][0]["main"],
                    "humidity": data["main"]["humidity"],
                    "city": input_data.city
                }
                
            except httpx.HTTPError as e:
                return {
                    "success": False,
                    "error": str(e)
                }
```

### React Component

```jsx
import { useWidgetProps } from 'chatjs-hooks';

export default function Weather() {
  const props = useWidgetProps();
  
  if (!props.success) {
    return <div style={{ color: 'red' }}>Error: {props.error}</div>;
  }
  
  return (
    <div style={{ padding: '20px' }}>
      <h1>Weather in {props.city}</h1>
      <div style={{ fontSize: '48px' }}>{props.temperature}°C</div>
      <p>{props.condition}</p>
      <p>Humidity: {props.humidity}%</p>
    </div>
  );
}
```

## HTTP Methods

### GET Request

```python
response = await client.get(
    "https://api.example.com/data",
    params={"key": "value"},
    headers={"Authorization": f"Bearer {token}"}
)
```

### POST Request

```python
response = await client.post(
    "https://api.example.com/create",
    json={"name": "value"},
    headers={"Content-Type": "application/json"}
)
```

### PUT Request

```python
response = await client.put(
    "https://api.example.com/update/123",
    json={"name": "new value"}
)
```

### DELETE Request

```python
response = await client.delete(
    "https://api.example.com/delete/123"
)
```

## Error Handling

### Status Codes

```python
async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        response = await client.get("https://api.example.com/data")
        
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        elif response.status_code == 404:
            return {"success": False, "error": "Not found"}
        elif response.status_code == 429:
            return {"success": False, "error": "Rate limit exceeded"}
        else:
            return {"success": False, "error": f"Error {response.status_code}"}
```

### Timeout Handling

```python
async def execute(self, input_data):
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get("https://slow-api.com/data")
            return {"success": True, "data": response.json()}
        except httpx.TimeoutException:
            return {"success": False, "error": "Request timeout"}
```

### Retry Logic

```python
async def execute(self, input_data):
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.example.com/data")
                response.raise_for_status()
                return {"success": True, "data": response.json()}
                
        except httpx.HTTPError as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                return {"success": False, "error": f"Failed after {max_retries} attempts"}
```

## Authentication

### API Key

```python
import os

API_KEY = os.getenv("WEATHER_API_KEY", "default_key")

async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            params={"apikey": API_KEY}
        )
```

### Bearer Token

```python
async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.example.com/data",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}
        )
```

### OAuth (Complex)

```python
# Use an OAuth library like authlib
from authlib.integrations.httpx_client import AsyncOAuth2Client

async def execute(self, input_data):
    client = AsyncOAuth2Client(
        client_id="your_client_id",
        client_secret="your_client_secret"
    )
    
    # Fetch token
    token = await client.fetch_token(
        "https://oauth.example.com/token"
    )
    
    # Make authenticated request
    response = await client.get("https://api.example.com/data")
    return {"data": response.json()}
```

## Multiple API Calls

### Sequential

```python
async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        # First call
        user_response = await client.get(f"https://api.example.com/users/{input_data.user_id}")
        user_data = user_response.json()
        
        # Second call (depends on first)
        posts_response = await client.get(f"https://api.example.com/users/{user_data['id']}/posts")
        posts_data = posts_response.json()
        
        return {
            "user": user_data,
            "posts": posts_data
        }
```

### Parallel

```python
import asyncio

async def execute(self, input_data):
    async with httpx.AsyncClient() as client:
        # Run in parallel
        weather_task = client.get("https://api.weather.com/data")
        news_task = client.get("https://api.news.com/headlines")
        stocks_task = client.get("https://api.stocks.com/prices")
        
        # Wait for all
        weather_resp, news_resp, stocks_resp = await asyncio.gather(
            weather_task,
            news_task,
            stocks_task
        )
        
        return {
            "weather": weather_resp.json(),
            "news": news_resp.json(),
            "stocks": stocks_resp.json()
        }
```

## Content Security Policy

### Why CSP?

ChatGPT restricts external connections for security. You must explicitly allow domains.

### Adding Domains

```python
widget_csp = {
    "connect_domains": [
        "https://api.example.com",        # Your API
        "https://auth.example.com"        # Auth endpoint
    ],
    "resource_domains": [
        "https://cdn.example.com",        # Images, fonts
        "https://images.example.com"      # Image CDN
    ]
}
```

### Wildcard Subdomains (Not Supported)

```python
# Doesn't work
"connect_domains": ["https://*.example.com"]

# List each subdomain
"connect_domains": [
    "https://api.example.com",
    "https://api2.example.com",
    "https://cdn.example.com"
]
```

## Real-World Examples

### GitHub API

```python
class GitHubRepoTool(BaseWidget):
    identifier = "github_repo"
    widget_csp = {
        "connect_domains": ["https://api.github.com"]
    }
    
    async def execute(self, input_data):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{input_data.owner}/{input_data.repo}",
                headers={
                    "Accept": "application/vnd.github.v3+json",
                    "User-Agent": "FastApps-Widget"
                }
            )
            
            if response.status_code == 200:
                repo = response.json()
                return {
                    "name": repo["name"],
                    "description": repo["description"],
                    "stars": repo["stargazers_count"],
                    "url": repo["html_url"]
                }
            else:
                return {"error": "Repository not found"}
```

### REST API with Pagination

```python
async def execute(self, input_data):
    all_items = []
    page = 1
    max_pages = 5
    
    async with httpx.AsyncClient() as client:
        while page <= max_pages:
            response = await client.get(
                "https://api.example.com/items",
                params={"page": page, "per_page": 100}
            )
            
            data = response.json()
            all_items.extend(data["items"])
            
            if not data.get("has_more"):
                break
            
            page += 1
    
    return {"items": all_items, "total": len(all_items)}
```

## Best Practices

1. **Always use async/await** - Don't block event loop
2. **Set timeouts** - Prevent hanging requests
3. **Handle all errors** - Network, HTTP, parsing errors
4. **Validate responses** - Check status codes and data structure
5. **Use proper CSP** - Add all domains you'll call
6. **Cache when possible** - Reduce API calls
7. **Rate limit** - Respect API limits
8. **Secure credentials** - Use environment variables

## Next Steps

- [Security](./07-SECURITY.md) - CSP and security best practices
- [Testing](./08-TESTING.md) - Testing tools and widgets
- [Deployment](./09-DEPLOYMENT.md) - Production deployment

