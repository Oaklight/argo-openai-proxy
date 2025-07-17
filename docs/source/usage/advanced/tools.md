# Tool Calls (Function Calling)

The experimental tool calls (function calling) interface has been available since version v2.7.5.alpha1, providing powerful capabilities for integrating AI models with external functions and APIs.

## What is Tool Calling?

**Important**: Tool calling is often misunderstood. Let's clarify what actually happens:

### The Reality of Tool Calling

1. **LLMs don't execute functions** - They cannot and do not run your code
2. **LLMs only see descriptions** - They work with JSON schemas that describe your functions
3. **LLMs make requests** - They tell you what function to call and with what arguments
4. **You do the work** - Your application executes the function and returns results
5. **LLMs process results** - They incorporate the function results into their response

### The Tool Calling Workflow

```
User: "What's the weather in Shanghai?"
  ↓
LLM: "I need to call get_weather function with location='Shanghai'"
  ↓
Your App: Executes get_weather("Shanghai") → {"temp": "22°C", "condition": "sunny"}
  ↓
LLM: "The weather in Shanghai is 22°C and sunny"
```

### What LLMs Actually See

When you provide a function schema, the LLM only sees the description:

```json
{
  "name": "get_weather",
  "description": "Get current weather for a location",
  "parameters": {
    "type": "object",
    "properties": {
      "location": { "type": "string", "description": "City name" }
    }
  }
}
```

The LLM has **no knowledge** of your actual implementation - it only knows what you tell it in the description.

## Tool Calling Rules and Guidelines

### Critical Rules to Follow

1. **Function descriptions are everything** - The LLM's decision-making is entirely based on your function descriptions. Write them clearly and accurately.

2. **You must provide both schema AND implementation** - Without helper libraries, you need to:
   - Write the actual function code
   - Manually compose the JSON schema that describes it
   - Ensure they match perfectly

3. **Validate all inputs** - Never trust function arguments from the LLM. Always validate and sanitize inputs before execution.

4. **Handle errors gracefully** - Functions can fail. Always return meaningful error messages that the LLM can understand and communicate to users.

5. **Keep functions focused** - Each function should do one thing well. Avoid complex multi-purpose functions.

6. **Provide complete results** - Return all relevant information the LLM needs to formulate a proper response.

7. **Use appropriate data types** - Match your function signatures with the JSON schema types you declare.

### Manual Schema Creation

If you're not using helper libraries like ToolRegistry, you must manually create JSON schemas:

```python
# Your function implementation
def calculate_tip(bill_amount: float, tip_percentage: float = 15.0) -> dict:
    """Calculate tip amount and total bill"""
    tip = bill_amount * (tip_percentage / 100)
    total = bill_amount + tip
    return {
        "tip_amount": round(tip, 2),
        "total_amount": round(total, 2),
        "tip_percentage": tip_percentage
    }

# You MUST also manually create the matching schema
tip_calculator_schema = {
    "type": "function",
    "function": {
        "name": "calculate_tip",
        "description": "Calculate tip amount and total bill for a restaurant check",
        "parameters": {
            "type": "object",
            "properties": {
                "bill_amount": {
                    "type": "number",
                    "description": "The bill amount before tip in dollars"
                },
                "tip_percentage": {
                    "type": "number",
                    "description": "Tip percentage (default: 15.0)",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["bill_amount"]
        }
    }
}
```

### Schema-Only Tools (Advanced Technique)

**Interesting fact**: You can provide tool schemas without actual implementations! This can be useful for:

1. **Prompting specific responses** - Guide the LLM to structure its thinking
2. **Placeholder functionality** - Indicate future features
3. **Testing and prototyping** - See how LLMs would use hypothetical tools

```python
# Schema for a "tool" that doesn't actually exist
fake_tool_schema = {
    "type": "function",
    "function": {
        "name": "analyze_user_sentiment",
        "description": "Analyze the emotional tone and sentiment of user messages",
        "parameters": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "The user message to analyze"
                },
                "context": {
                    "type": "string",
                    "description": "Additional context about the conversation"
                }
            },
            "required": ["message"]
        }
    }
}

# When the LLM "calls" this function, you can:
# 1. Return a mock response
# 2. Perform the analysis manually
# 3. Redirect to a different service
# 4. Simply acknowledge the request
```

**Use cases for schema-only tools**:
- **Guided reasoning**: Make the LLM think through problems step-by-step
- **Structured output**: Force the LLM to format responses in specific ways
- **Feature planning**: Test how users would interact with planned features
- **Debugging**: Understand what tools the LLM thinks it needs

### Function Description Best Practices

```python
# ❌ Poor description
def get_data(x):
    """Gets data"""
    pass

# ✅ Good description
def get_weather(location: str, units: str = "metric") -> dict:
    """Get current weather information for a specific location

    Args:
        location: City name or "City, Country" format (e.g., "Tokyo" or "Paris, France")
        units: Temperature units - "metric" for Celsius, "imperial" for Fahrenheit

    Returns:
        Dictionary containing temperature, humidity, conditions, and forecast

    Raises:
        ValueError: If location is not found or invalid
        ConnectionError: If weather service is unavailable
    """
    pass
```

### Error Handling Rules

```python
def safe_function(user_input: str) -> dict:
    """Example of proper error handling for tool calls"""
    try:
        # Validate input
        if not user_input or len(user_input) > 1000:
            return {
                "error": "Invalid input: must be 1-1000 characters",
                "success": False
            }

        # Process safely
        result = process_input(user_input)

        return {
            "result": result,
            "success": True
        }

    except Exception as e:
        return {
            "error": f"Processing failed: {str(e)}",
            "success": False
        }
```

## Overview

Tool calls enable AI models to request function executions by:

- Analyzing function descriptions (JSON schemas)
- Determining when functions are needed based on user queries
- Generating function call requests with appropriate arguments
- Processing function results you provide back to them
- Integrating results into natural language responses

## Availability

- **Available on**: Both streaming and non-streaming **chat completion** endpoints
- **Supported endpoints**: `/v1/chat/completions`
- **Not supported**: Argo passthrough (`/v1/chat`) and legacy completion endpoints (`/v1/completions`)
- **Status**: Experimental feature under active development

## Streaming Behavior

When using function calling with streaming:

- **Pseudo stream is automatically enforced** regardless of your configuration
- This ensures reliable function call processing with the current prompting-based implementation
- Users will not notice this automatic switch as the experience remains smooth
- The streaming mode switch is transparent and maintains a consistent user experience

## Supported Models

All chat models support tool calls.

## Basic Usage Example

**Remember**: Without helper libraries, you need both function implementation AND manual schema creation.

```python
import openai
import json

client = openai.OpenAI(
    base_url="http://localhost:44497/v1",
    api_key="dummy"
)

# Step 1: Implement your function
def get_weather(location: str) -> dict:
    """Get current weather for a location"""
    # Your weather API implementation here
    # This is just a mock response
    return {
        "location": location,
        "temperature": "22°C",
        "condition": "sunny",
        "humidity": "65%"
    }

# Step 2: Manually create the JSON schema (if not using helper libraries)
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",  # Must match your function name
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or 'City, Country' format"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Step 3: Function execution handler
def execute_function_call(function_name: str, arguments: dict):
    """Execute the actual function based on LLM's request"""
    if function_name == "get_weather":
        return get_weather(**arguments)
    else:
        return {"error": f"Unknown function: {function_name}"}

# Step 4: Make a request with tool calls
response = client.chat.completions.create(
    model="argo:gpt-4o",
    messages=[
        {"role": "user", "content": "What's the weather in New York?"}
    ],
    tools=tools,
    tool_choice="auto"
)

# Step 5: Handle tool calls in the response
if response.choices[0].message.tool_calls:
    for tool_call in response.choices[0].message.tool_calls:
        function_name = tool_call.function.name
        function_args = json.loads(tool_call.function.arguments)
        
        # Execute the actual function
        result = execute_function_call(function_name, function_args)
        
        print(f"Function: {function_name}")
        print(f"Arguments: {function_args}")
        print(f"Result: {result}")
```

**Key Points**:
- The LLM only sees the schema in `tools`, not your `get_weather` function
- You must manually ensure the schema matches your function signature
- You are responsible for executing the function when the LLM requests it

## Tool Definition Structure

### Function Schema

```json
{
  "type": "function",
  "function": {
    "name": "function_name",
    "description": "Clear description of what the function does",
    "parameters": {
      "type": "object",
      "properties": {
        "param1": {
          "type": "string",
          "description": "Description of parameter 1"
        },
        "param2": {
          "type": "number",
          "description": "Description of parameter 2"
        }
      },
      "required": ["param1"]
    }
  }
}
```

### Parameter Types

Supported parameter types:

- `string`: Text values
- `number`: Numeric values (integers and floats)
- `boolean`: True/false values
- `array`: Lists of values
- `object`: Nested objects

### Advanced Parameter Schema

```json
{
  "type": "object",
  "properties": {
    "location": {
      "type": "string",
      "description": "City and state, e.g. San Francisco, CA"
    },
    "temperature_unit": {
      "type": "string",
      "enum": ["celsius", "fahrenheit"],
      "description": "Temperature unit"
    },
    "include_forecast": {
      "type": "boolean",
      "description": "Whether to include forecast data"
    },
    "days": {
      "type": "number",
      "minimum": 1,
      "maximum": 7,
      "description": "Number of forecast days"
    }
  },
  "required": ["location"]
}
```

## Tool Choice Options

Control when and how tools are called:

### `auto` (Default)

```python
tool_choice="auto"
```

Model decides whether to call functions based on the conversation context.

### `none`

```python
tool_choice="none"
```

Model will not call any functions, even if tools are provided.

### Specific Function

```python
tool_choice={
    "type": "function",
    "function": {"name": "get_weather"}
}
```

Forces the model to call a specific function.

## Handling Tool Call Responses

### Complete Workflow Example

```python
def execute_function_call(function_name, arguments):
    """Execute the actual function call"""
    if function_name == "get_weather":
        # Your weather API implementation
        return get_weather_data(arguments["location"])
    elif function_name == "calculate":
        # Your calculation implementation
        return perform_calculation(arguments)
    else:
        return {"error": "Unknown function"}

# Initial request
response = client.chat.completions.create(
    model="argo:gpt-4o",
    messages=[
        {"role": "user", "content": "What's the weather in Paris?"}
    ],
    tools=tools,
    tool_choice="auto"
)

messages = [{"role": "user", "content": "What's the weather in Paris?"}]

# Handle tool calls
if response.choices[0].message.tool_calls:
    # Add assistant message with tool calls
    messages.append(response.choices[0].message)

    # Execute each tool call
    for tool_call in response.choices[0].message.tool_calls:
        function_result = execute_function_call(
            tool_call.function.name,
            json.loads(tool_call.function.arguments)
        )

        # Add tool response
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": json.dumps(function_result)
        })

    # Get final response
    final_response = client.chat.completions.create(
        model="argo:gpt-4o",
        messages=messages
    )

    print(final_response.choices[0].message.content)
```

## Best Practices

### Understanding the LLM's Perspective

Remember: **The LLM only sees your function descriptions, not your code.** Design your schemas accordingly:

```python
# The LLM sees this schema:
{
  "name": "search_database",
  "description": "Search for products in the inventory database",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "Search term (product name, category, or SKU)"
      },
      "category": {
        "type": "string",
        "enum": ["electronics", "clothing", "books", "home"],
        "description": "Filter by product category"
      }
    },
    "required": ["query"]
  }
}

# But NOT this implementation:
def search_database(query, category=None):
    # Your actual database logic here
    pass
```

### Function Design Principles

1. **Descriptions are your interface** - Write function descriptions as if explaining to a human assistant
2. **Be explicit about constraints** - Use enums, ranges, and detailed descriptions
3. **Anticipate misuse** - LLMs might call functions in unexpected ways
4. **Design for conversation** - Functions should return information suitable for natural language responses

### Schema Design Rules

```python
# ❌ Vague schema
{
  "name": "process_data",
  "description": "Processes data",
  "parameters": {
    "type": "object",
    "properties": {
      "data": {"type": "string"}
    }
  }
}

# ✅ Clear schema
{
  "name": "analyze_sales_data",
  "description": "Analyze sales performance for a specific time period and generate insights",
  "parameters": {
    "type": "object",
    "properties": {
      "start_date": {
        "type": "string",
        "description": "Start date in YYYY-MM-DD format"
      },
      "end_date": {
        "type": "string",
        "description": "End date in YYYY-MM-DD format"
      },
      "metrics": {
        "type": "array",
        "items": {"type": "string", "enum": ["revenue", "units_sold", "profit_margin"]},
        "description": "Which metrics to include in analysis"
      }
    },
    "required": ["start_date", "end_date"]
  }
}
```

### Implementation Guidelines

1. **Validate everything** - Never trust LLM-generated arguments
2. **Return structured data** - Use consistent response formats
3. **Handle edge cases** - LLMs can generate unexpected but valid inputs
4. **Provide context** - Include relevant metadata in responses

### Security Considerations

1. **Input validation**: Always validate function arguments
2. **Sandboxing**: Run functions in controlled environments
3. **Rate limiting**: Implement rate limiting for expensive operations
4. **Access control**: Restrict function access based on user permissions

### Performance Optimization

1. **Async functions**: Use async functions for I/O operations
2. **Caching**: Cache function results when appropriate
3. **Timeout handling**: Implement timeouts for long-running functions
4. **Resource management**: Properly manage resources (connections, files, etc.)

## Limitations and Known Issues

### Current Limitations

- **Experimental status**: Feature is under active development
- **Prompting-based**: Current implementation uses prompting rather than native function calling
- **Streaming behavior**: Automatically switches to pseudo-stream mode
- **Response API**: Tool call support for response API is under development

### Planned Improvements

- Native function calling support (work in progress)
- Enhanced streaming support
- Response API integration
- Performance optimizations

## Troubleshooting

### Common Issues

**Tool calls not triggered**:

- Check function descriptions are clear and relevant
- Verify tool_choice setting
- Ensure model supports function calling

**Invalid function arguments**:

- Validate parameter schema
- Check required parameters
- Review parameter descriptions

**Function execution errors**:

- Implement proper error handling
- Validate input arguments
- Check function implementation

### Debug Tips

1. **Enable verbose logging**: Use `--verbose` flag to see detailed logs
2. **Test function schemas**: Validate JSON schema before use
3. **Monitor tool calls**: Log all tool calls and responses
4. **Use simple functions first**: Start with basic functions before complex ones

## Integration with ToolRegistry

For simplified tool management and automatic schema generation, see the [ToolRegistry Integration](toolregistry.md) guide.

## Examples and Use Cases

### Weather Service Integration

```python
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
