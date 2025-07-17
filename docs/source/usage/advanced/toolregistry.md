# ToolRegistry Integration

A lightweight yet powerful Python helper library is available for various tool handling: [ToolRegistry](https://github.com/Oaklight/ToolRegistry).

## Installation

```bash
pip install toolregistry
```

## Basic Usage with ToolRegistry

```python
from toolregistry import ToolRegistry
import openai

# Create registry and register functions
registry = ToolRegistry()

@registry.register
def get_weather(location: str) -> dict:
    """Get current weather for a location"""
    # Your weather implementation
    return {"location": location, "temperature": "22°C", "condition": "sunny"}

@registry.register
def calculate(expression: str) -> float:
    """Calculate a mathematical expression"""
    # Safe calculation implementation
    return eval(expression)  # Use safe_eval in production

# Use with OpenAI client
client = openai.OpenAI(
    base_url="http://localhost:44497/v1",
    api_key="dummy"
)

# Get tools from registry
tools = registry.get_tools()

# Make request
response = client.chat.completions.create(
    model="argo:gpt-4o",
    messages=[{"role": "user", "content": "What's 15 * 23?"}],
    tools=tools
)

# Execute tool calls using registry
if response.choices[0].message.tool_calls:
    results = registry.execute_tool_calls(response.choices[0].message.tool_calls)
    print(results)
```

## Advanced ToolRegistry Features

### Automatic Function Registration

ToolRegistry automatically generates OpenAI-compatible tool schemas from your Python functions:

```python
@registry.register
def search_database(query: str, table: str, limit: int = 10) -> list:
    """Search database with SQL query
    
    Args:
        query: SQL query string
        table: Table name to search
        limit: Maximum number of results to return
    
    Returns:
        List of matching records
    """
    # Your database implementation
    pass
```

### Type Hints Support

ToolRegistry leverages Python type hints to generate accurate parameter schemas:

```python
from typing import List, Optional, Union

@registry.register
def process_data(
    data: List[dict], 
    operation: str, 
    threshold: Optional[float] = None,
    output_format: Union[str, None] = "json"
) -> dict:
    """Process data with specified operation"""
    # Your data processing implementation
    pass
```

### Error Handling

ToolRegistry provides built-in error handling for tool execution:

```python
# Registry automatically handles exceptions
try:
    results = registry.execute_tool_calls(tool_calls)
except Exception as e:
    print(f"Tool execution failed: {e}")
```

## Integration Examples

### Weather Service Integration

```python
@registry.register
def get_weather(location: str, units: str = "metric") -> dict:
    """Get weather information for a location"""
    # Integration with weather API
    import requests
    
    api_key = "your_api_key"
    url = f"http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": location,
        "appid": api_key,
        "units": units
    }
    
    response = requests.get(url, params=params)
    return response.json()
```

### Database Queries

```python
@registry.register
def search_database(query: str, table: str) -> list:
    """Search database with SQL query"""
    # Safe database query implementation
    import sqlite3
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Use parameterized queries for security
    safe_query = f"SELECT * FROM {table} WHERE content LIKE ?"
    cursor.execute(safe_query, (f"%{query}%",))
    
    results = cursor.fetchall()
    conn.close()
    
    return results
```

### File Operations

```python
@registry.register
def read_file(filename: str) -> str:
    """Read contents of a file"""
    # Secure file reading with path validation
    import os
    from pathlib import Path
    
    # Validate file path for security
    safe_path = Path(filename).resolve()
    if not safe_path.is_file():
        raise ValueError("Invalid file path")
    
    with open(safe_path, 'r', encoding='utf-8') as f:
        return f.read()
```

### API Integrations

```python
@registry.register
def call_external_api(endpoint: str, method: str = "GET", data: dict = None) -> dict:
    """Make API calls to external services"""
    # HTTP client implementation with security checks
    import requests
    
    allowed_domains = ["api.example.com", "secure-api.service.com"]
    
    # Validate endpoint domain
    from urllib.parse import urlparse
    parsed_url = urlparse(endpoint)
    if parsed_url.netloc not in allowed_domains:
        raise ValueError("Unauthorized API endpoint")
    
    if method.upper() == "GET":
        response = requests.get(endpoint)
    elif method.upper() == "POST":
        response = requests.post(endpoint, json=data)
    else:
        raise ValueError("Unsupported HTTP method")
    
    return response.json()
```

## Best Practices with ToolRegistry

### Function Documentation

Always provide clear docstrings for your registered functions:

```python
@registry.register
def complex_calculation(
    numbers: List[float], 
    operation: str, 
    precision: int = 2
) -> dict:
    """Perform complex mathematical operations on a list of numbers
    
    Args:
        numbers: List of numbers to process
        operation: Type of operation ('sum', 'average', 'median', 'std')
        precision: Number of decimal places for results
    
    Returns:
        Dictionary containing the result and metadata
        
    Raises:
        ValueError: If operation is not supported
        TypeError: If numbers list contains non-numeric values
    """
    # Implementation here
    pass
```

### Security Considerations

1. **Input Validation**: Always validate function arguments
2. **Sandboxing**: Run functions in controlled environments
3. **Access Control**: Restrict function access based on permissions
4. **Resource Limits**: Implement timeouts and resource limits

```python
@registry.register
def secure_function(user_input: str) -> str:
    """Example of secure function implementation"""
    # Input validation
    if not isinstance(user_input, str):
        raise TypeError("Input must be a string")
    
    if len(user_input) > 1000:
        raise ValueError("Input too long")
    
    # Sanitize input
    import re
    sanitized = re.sub(r'[^\w\s-]', '', user_input)
    
    # Process with timeout
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("Function execution timeout")
    
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)  # 30 second timeout
    
    try:
        # Your function logic here
        result = process_input(sanitized)
        return result
    finally:
        signal.alarm(0)  # Cancel timeout
```

### Performance Optimization

1. **Async Support**: Use async functions for I/O operations
2. **Caching**: Cache function results when appropriate
3. **Resource Management**: Properly manage connections and resources

```python
import asyncio
from functools import lru_cache

@registry.register
async def async_api_call(endpoint: str) -> dict:
    """Async API call with caching"""
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        async with session.get(endpoint) as response:
            return await response.json()

@registry.register
@lru_cache(maxsize=128)
def cached_calculation(value: float) -> float:
    """Expensive calculation with caching"""
    # Simulate expensive operation
    import time
    time.sleep(1)
    return value ** 2
```

## Troubleshooting ToolRegistry

### Common Issues

**Function not registered properly**:
- Ensure you're using the `@registry.register` decorator
- Check that function has proper type hints
- Verify function docstring is present

**Tool execution fails**:
- Check function implementation for errors
- Validate input parameters
- Review error logs for specific issues

**Schema generation problems**:
- Ensure all parameters have type hints
- Use supported types (str, int, float, bool, list, dict)
- Provide clear parameter descriptions in docstring

### Debug Tips

1. **Inspect generated schemas**: Use `registry.get_tools()` to see generated schemas
2. **Test functions individually**: Call functions directly before using with AI
3. **Enable logging**: Use Python logging to track function execution
4. **Validate schemas**: Ensure generated schemas match OpenAI requirements

```python
# Debug example
registry = ToolRegistry()

@registry.register
def debug_function(param: str) -> str:
    """Debug function for testing"""
    return f"Processed: {param}"

# Inspect generated schema
tools = registry.get_tools()
print(json.dumps(tools, indent=2))

# Test function directly
result = debug_function("test")
print(f"Direct call result: {result}")