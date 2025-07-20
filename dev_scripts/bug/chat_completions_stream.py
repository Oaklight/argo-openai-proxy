import os

import httpx
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "http://localhost:44498")
MODEL = os.getenv("MODEL", "argo:gpt-4o")

CHAT_ENDPOINT = f"{BASE_URL}/v1/chat/completions"

print("Running Chat Test with Messages")

# Define the request payload using the "messages" field
# Define the request payload using the "messages" field
# payload = {
#     "model": MODEL,
#     "messages": [
#         {
#             "role": "user",
#             "content": "Tell me something interesting about quantum mechanics.",
#         },
#     ],
#     "user": "test_user",  # This will be overridden by the proxy_request function
#     "stream": True,
#     # "max_tokens": 5,
# }
payload = {
    "model": MODEL,
    "temperature": 0,
    "messages": [
        {
            "role": "system",
            "content": "You are Kilo Code, a highly skilled software engineer with extensive knowledge in many programming languages, frameworks, design patterns, and best practices.",
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Hi, I need help with a coding task."},
                {
                    "type": "text",
                    "text": "make a python function that takes a list of integers and returns the sum of the list",
                },
            ],
        },
    ],
    "stream": True,
    "stream_options": {"include_usage": True},
}

headers = {
    "Content-Type": "application/json",
}


with httpx.stream(
    "POST", CHAT_ENDPOINT, json=payload, headers=headers, timeout=60.0
) as response:
    print("Status Code: ", response.status_code)
    print("Headers: ", response.headers)
    print("Streaming Response: ")

    # Read the resonse chunks as they arrive
    for chunk in response.iter_bytes():
        if chunk:
            print(chunk.decode(errors="replace"), end="", flush=True)
