import os
import time

import httpx

MODEL = os.getenv("MODEL", "gpt4o")

# API endpoint to POST
url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"

# Data to match the working cURL format

data = {
    "user": "<ENTER YOUR ANL DOMAIN USERNMAE>",
    "model": MODEL,
    # --> OPTION 1 - Send system/prompt fields:
    # "system": "You are a large language model with the name Argo.",
    # "prompt": ["Tell me something interesting about quantum mechanics."],
    # --> OPTION 2 - Send messages object field:
    "messages": [
        {
            "role": "system",
            "content": "You are a large language model with the name Argo",
        },
        {
            "role": "user",
            "content": "Tell me something interesting about quantum mechanics.",
        },
    ],
    "stop": [],
    "temperature": 0.1,
}

# Headers for streaming
headers = {
    "Content-Type": "application/json",
    "Accept": "text/plain",
    "Cache-Control": "no-cache",
    "Accept-Encoding": "identity",  # Important: Disable gzip compression
}

# Use httpx to send the request with streaming enabled
# Retry loop to continue calling until success
attempt = 1
while True:
    try:
        with httpx.stream(
            "POST", url, json=data, headers=headers, timeout=120.0
        ) as response:
            if response.status_code == 200:
                print(f"Connected successfully (attempt {attempt})")
                print(f" Status Code: {response.status_code}")
                print("Streaming Response:")
                print("-" * 50)

                for chunk in response.iter_text():
                    if chunk:
                        print(chunk, end="", flush=True)

                print(f"\n{'-' * 50}")
                print("Stream completed.")
                break  # Exit the loop on success

            else:
                print(
                    f"Attempt {attempt} failed (status {response.status_code}), retrying..."
                )

    except httpx.TimeoutException:
        print("Request timed out")
    except Exception as e:
        print(f"Attempt {attempt} failed ({e}), retrying...")

    attempt += 1
    time.sleep(1)  # Brief pause between retries
