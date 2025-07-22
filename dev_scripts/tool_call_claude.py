import json

import httpx

# API endpoint to POST
url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"

# Data to be sent as a POST in JSON format
claude_styled_messages = [
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

openai_styled_messages = [
    {
        "role": "user",
        "content": "Could you check the current stock price of Apple for me?",
    },
    {  # assistant tool call
        "role": "assistant",
        "content": "Let me check Apple's current stock price for you:",
        "tool_calls": [
            {
                "id": "call_abc123",
                "type": "function",
                "function": {
                    "name": "get_stock_price",
                    "arguments": '{"ticker": "AAPL"}'
                }
            }
        ]
    },
    {  # tool response
        "role": "tool",
        "tool_call_id": "call_abc123",
        "content": "182.45"
    },
]

data = {
    "user": "pding",
    "model": "claudesonnet4",
    # "messages": claude_styled_messages,
    "messages": openai_styled_messages,
    "stop": [],
    "temperature": 0,
    "tools": [
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
    ],
    "tool_choice": {"type": "auto"},
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
print("LLM response: ", response.json()["response"])
