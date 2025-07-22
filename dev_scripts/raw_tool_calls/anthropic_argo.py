import json

import httpx

# API endpoint to POST
url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"

# Data to be sent as a POST in JSON format
working_anthropic_styled_messages = [
    {
        "role": "user",
        "content": "Could you check the current stock price of Apple for me?",
    },
    {
        "role": "assistant",
        "content": "Let me check Apple's current stock price for you:",
    },
    {  # fake tool call from the assistant
        "role": "assistant",
        "content": [
            {
                # "id": "toolu_vrtx_01LiZkD1myhnDz7gcoEe4Y5A",
                "id": "tu_vrtx_01LiZkD1my",
                "input": {"ticker": "AAPL"},
                "name": "get_stock_price",
                "type": "tool_use",
            }
        ],
    },
    {  # fake tool response from the user
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                # "tool_use_id": "toolu_vrtx_01LiZkD1myhnDz7gcoEe4Y5A",
                "tool_use_id": "tu_vrtx_01LiZkD1my",
                "content": "182.45",
            }
        ],
    },
]
working_anthropic_styled_tools = [
    {
        "name": "get_stock_price",
        "description": "Retrieves the current stock price for a given ticker symbol. The ticker symbol must be a valid symbol for a publicly traded company on a major US stock exchange like NYSE or NASDAQ. The tool will return the latest trade price in USD. It should be used when the user asks about the current or most recent price of a specific stock. It will not provide any other information about the stock or company.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "The stock ticker symbol, e.g. AAPL for Apple Inc.",
                }
            },
            "required": ["ticker"],
        },
    }
]

anthropic_styled_messages = [
    {
        "role": "user",
        "content": "\nI have a few test results from multiple runs. Please compute the averages of the metrics for each category. The input is as \n$ EXEC_MODE=thread python examples/test_toolregistry_concurrency.py \n---------- Native Func Tool ----------\n['local_add', 'local_subtract', 'local_multiply', 'local_divide']\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0202 seconds\nThroughput: 4957.16 calls/second\n---------- Native Class Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0077 seconds\nThroughput: 12963.79 calls/second\n---------- OpenAPI Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 3.4877 seconds\nThroughput: 28.67 calls/second\n---------- MCP SSE Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 3.5374 seconds\nThroughput: 28.27 calls/second\n\n$ EXEC_MODE=thread python examples/test_toolregistry_concurrency.py \n---------- Native Func Tool ----------\n['local_add', 'local_subtract', 'local_multiply', 'local_divide']\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0205 seconds\nThroughput: 4879.93 calls/second\n---------- Native Class Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0094 seconds\nThroughput: 10621.45 calls/second\n---------- OpenAPI Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 3.4220 seconds\nThroughput: 29.22 calls/second\n---------- MCP SSE Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 3.6341 seconds\nThroughput: 27.52 calls/second\n\n$ EXEC_MODE=thread python examples/test_toolregistry_concurrency.py \n---------- Native Func Tool ----------\n['local_add', 'local_subtract', 'local_multiply', 'local_divide']\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0223 seconds\nThroughput: 4479.42 calls/second\n---------- Native Class Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0078 seconds\nThroughput: 12789.85 calls/second\n---------- OpenAPI Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 3.6604 seconds\nThroughput: 27.32 calls/second\n---------- MCP SSE Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 3.7925 seconds\nThroughput: 26.37 calls/second\n\n$ EXEC_MODE=process python examples/test_toolregistry_concurrency.py \n---------- Native Func Tool ----------\n['local_add', 'local_subtract', 'local_multiply', 'local_divide']\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0452 seconds\nThroughput: 2210.06 calls/second\n---------- Native Class Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0319 seconds\nThroughput: 3130.01 calls/second\n---------- OpenAPI Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.2229 seconds\nThroughput: 448.58 calls/second\n---------- MCP SSE Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.7544 seconds\nThroughput: 132.56 calls/second\n\n$ EXEC_MODE=process python examples/test_toolregistry_concurrency.py \n---------- Native Func Tool ----------\n['local_add', 'local_subtract', 'local_multiply', 'local_divide']\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0410 seconds\nThroughput: 2439.80 calls/second\n---------- Native Class Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0330 seconds\nThroughput: 3026.91 calls/second\n---------- OpenAPI Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.2221 seconds\nThroughput: 450.15 calls/second\n---------- MCP SSE Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.7536 seconds\nThroughput: 132.70 calls/second\n\n$ EXEC_MODE=process python examples/test_toolregistry_concurrency.py \n---------- Native Func Tool ----------\n['local_add', 'local_subtract', 'local_multiply', 'local_divide']\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0413 seconds\nThroughput: 2421.93 calls/second\n---------- Native Class Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.0348 seconds\nThroughput: 2875.06 calls/second\n---------- OpenAPI Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.2197 seconds\nThroughput: 455.11 calls/second\n---------- MCP SSE Tool ----------\nGot 100 results out of 100 calls.\nSuccess rate: 100.00% (100/100)\nExecuted 100 tool calls in 0.7572 seconds\nThroughput: 132.06 calls/second\n\n",
    },
    {
        "content": [
            {
                "id": "toolu_vrtx_01PerGNoufY8rBddJ5yqpZtM",
                "input": {"expression": "(4957.16 + 4879.93 + 4479.42) / 3"},
                "name": "calculator-evaluate",
                "type": "tool_use",
                "cache_control": None,
            },
        ],
        "role": "assistant",
    },
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": "toolu_vrtx_01PerGNoufY8rBddJ5yqpZtM",
                "content": "{'result': 4772.17, 'tool_call': {'arguments': '{\"expression\": \"(4957.16 + 4879.93 + 4479.42) / 3\"}', 'name': 'calculator-evaluate'}}",
            }
        ],
    },
]

anthropic_styled_tools = [
    {
        "input_schema": {
            "type": "object",
            "properties": {
                "with_help": {
                    "anyOf": [{"type": "boolean"}, {"type": "null"}],
                    "default": "false",
                    "title": "With Help",
                }
            },
            "required": None,
        },
        "name": "calculator-list_allowed_fns",
        "cache_control": None,
        "description": "Returns a JSON string of allowed functions for the evaluate method with their descriptions.\n\n        Each key is the name of an allowed function, and the value is its help message.\n        This allows quick access to both the list of functions and their descriptions without needing multiple queries.\n\n        Args:\n            with_help (bool, optional): If True, includes descriptions of each function. Defaults to False.\n\n        Returns:\n            str: A JSON string containing the allowed functions, if with_help is True, their descriptions.\n        ",
        "type": "custom",
    },
    {
        "input_schema": {
            "type": "object",
            "properties": {"fn_name": {"title": "Fn Name", "type": "string"}},
            "required": ["fn_name"],
        },
        "name": "calculator-help",
        "cache_control": None,
        "description": "Returns the help documentation for a specific function used in the evaluate method.\n\n        Args:\n            fn_name (str): Name of the function to get help for.\n\n        Returns:\n            str: Help documentation for the specified function.\n\n        Raises:\n            ValueError: If the function name is not recognized.\n        ",
        "type": "custom",
    },
    {
        "input_schema": {
            "type": "object",
            "properties": {"expression": {"title": "Expression", "type": "string"}},
            "required": ["expression"],
        },
        "name": "calculator-evaluate",
        "cache_control": None,
        "description": 'Evaluates a mathematical expression.\n\n        The `expression` can use named functions like `add(2, 3)` or native operators like `2 + 3`. Pay attention to operator precedence and use parentheses to ensure the intended order of operations. For example: `"add(2, 3) * pow(2, 3) + sqrt(16)"` or `"(2 + 3) * (2 ** 3) + sqrt(16)"` or mixed.\n\n        - Use `list_allowed_fns()` to view available functions. Set `with_help` to `True` to include function signatures and docstrings.\n        - Use `help` for detailed information on specific functions.\n\n        **Note**: If an error occurs due to an invalid expression, query the `help` method to check the function usage and ensure it is listed by `list_allowed_fns()`.\n\n        Args:\n            expression (str): Mathematical expression to evaluate.\n\n        Returns:\n            Union[float, int, bool]: Result of the evaluation.\n\n        Raises:\n            ValueError: If the expression is invalid or evaluation fails.\n        ',
        "type": "custom",
    },
]

anthropic_styled_tool_choice = {"type": "auto"}

data = {
    "user": "pding",
    "model": "claudesonnet4",
    # "messages": claude_styled_messages,
    "messages": anthropic_styled_messages,
    "stop": [],
    "temperature": 0,
    "tools": anthropic_styled_tools,
    "tool_choice": anthropic_styled_tool_choice,
    # "type": "custom",
}
# Convert the dict to JSON
payload = json.dumps(data)

# Add a header stating that the content type is JSON
headers = {"Content-Type": "application/json"}

# Send POST request
response = httpx.post(url, data=payload, headers=headers)

# Receive the response data
print("Status Code:", response.status_code)
try:
    print("LLM response: ", response.json()["response"])
except Exception as e:
    print(f"Error parsing JSON response: {e}")
    print("Raw response text: ", response.text)
