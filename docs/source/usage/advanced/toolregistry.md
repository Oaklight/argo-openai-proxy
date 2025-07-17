# ToolRegistry Integration

ToolRegistry is a lightweight yet powerful Python tool management library for handling various tool calls: [ToolRegistry](https://github.com/Oaklight/ToolRegistry).

## Installation

```bash
pip install toolregistry
```

For additional feature modules, you can use:

```bash
pip install toolregistry[mcp,openapi,langchain]
```

## Basic Usage

### Registering Tools

```python
from toolregistry import ToolRegistry

registry = ToolRegistry()

@registry.register
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@registry.register
def subtract(a: int, b: int) -> int:
    """Subtract the second number from the first."""
    return a - b
```

### Getting Tool JSON Schema

```python
# Get OpenAI-compatible tool JSON schema
tools_json = registry.get_tools_json(api_format="openai-chatcompletion")
```

Supported API formats:

- `openai-chatcompletion` or `openai` (default)
- `openai-response`

## Integration with OpenAI-Compatible APIs

```python
import openai
from toolregistry import ToolRegistry

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

# Use OpenAI client
client = openai.OpenAI(
    base_url="http://localhost:44497/v1",
    api_key="dummy"
)

# Get tools from registry
tools = registry.get_tools_json()

# Send request
response = client.chat.completions.create(
    model="argo:gpt-4o",
    messages=[{"role": "user", "content": "What's 15 * 23?"}],
    tools=tools
)

# Execute tool calls using registry
if response.choices[0].message.tool_calls:
    tool_calls = response.choices[0].message.tool_calls

    # Execute tool calls
    tool_responses = registry.execute_tool_calls(tool_calls)
    print(tool_responses)

    # Reconstruct assistant and tool call messages
    assistant_tool_messages = registry.recover_tool_call_assistant_message(
        tool_calls, tool_responses
    )

    # Extend message history
    messages = [{"role": "user", "content": "What's 15 * 23?"}]
    messages.extend(assistant_tool_messages)

    # Get final response
    final_response = client.chat.completions.create(
        model="argo:gpt-4o",
        messages=messages
    )

    print(final_response.choices[0].message.content)
```

## Advanced Features

### Accessing Available Tools

```python
# Get list of available tool names
available_tools = registry.get_available_tools()
print(available_tools)  # ['add', 'subtract']

# Access as callable functions
add_func = registry.get_callable('add')
result = add_func(1, 2)  # 3

# Or use __getitem__ method
add_func = registry['add']
result = add_func(4, 5)  # 9

# Access as Tool objects
add_tool = registry.get_tool("add")
value = add_tool.run({"a": 7, "b": 8})  # 15.0
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

### Concurrent Execution Modes

By default, `execute_tool_calls` uses process mode to execute tool calls in parallel:

```python
# Default uses process mode
tool_responses = registry.execute_tool_calls(tool_calls)

# Explicitly specify execution mode
tool_responses = registry.execute_tool_calls(tool_calls, execution_mode="process")
```

## Integrating Other Tool Sources

### MCP Tool Integration

```python
# Requires installation: pip install toolregistry[mcp]
registry.register_from_mcp(server_config)
```

### OpenAPI Tool Integration

```python
# Requires installation: pip install toolregistry[openapi]
registry.register_from_openapi(openapi_spec)
```

### LangChain Tool Integration

```python
# Requires installation: pip install toolregistry[langchain]
registry.register_from_langchain(langchain_tools)
```

### Class Tool Integration

```python
registry.register_from_class(tool_class)
```

## Best Practices

### Function Documentation

Always provide clear docstrings for registered functions:

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
    # Implementation code
    pass
```

### Security Considerations

1. **Input Validation**: Always validate function parameters
2. **Sandboxing**: Run functions in controlled environments
3. **Access Control**: Restrict function access based on permissions
4. **Resource Limits**: Implement timeouts and resource constraints

### Error Handling

ToolRegistry provides built-in error handling for tool execution:

```python
try:
    results = registry.execute_tool_calls(tool_calls)
except Exception as e:
    print(f"Tool execution failed: {e}")
```

## Troubleshooting

### Common Issues

**Function not registered correctly**:

- Ensure you're using the `@registry.register` decorator
- Check that the function has proper type hints
- Verify that function docstring exists

**Tool execution failures**:

- Check function implementation for errors
- Verify input parameters
- Review error logs for specific issues

**Schema generation problems**:

- Ensure all parameters have type hints
- Use supported types (str, int, float, bool, list, dict)
- Provide clear parameter descriptions in docstrings

### Debugging Tips

1. **Check generated schema**: Use `registry.get_tools_json()` to view the generated schema
2. **Test functions separately**: Call functions directly before using with AI
3. **Enable logging**: Use Python logging to track function execution
4. **Validate schema**: Ensure generated schema meets OpenAI requirements

```python
# Debugging example
import json

registry = ToolRegistry()

@registry.register
def debug_function(param: str) -> str:
    """Debug function for testing"""
    return f"Processed: {param}"

# Check generated schema
tools = registry.get_tools_json()
print(json.dumps(tools, indent=2))

# Test function directly
result = debug_function("test")
print(f"Direct call result: {result}")
```

## More Information

For detailed examples and advanced usage, please refer to:

- [ToolRegistry Official Documentation](https://github.com/Oaklight/ToolRegistry)
- [Concurrency Modes Guide](https://toolregistry.readthedocs.io/en/latest/usage/concurrency_modes.html)
- [Best Practices](https://toolregistry.readthedocs.io/en/latest/usage/best_practices.html)
