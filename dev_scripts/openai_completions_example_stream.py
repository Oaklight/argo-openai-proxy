import httpx

# Configuration
BASE_URL = "https://api.siliconflow.cn"  # Update if your server is running on a different host/port
MODEL = "Qwen/Qwen2-1.5B-Instruct"
API_KEY = "sk-your-siliconflow-api-key"

# BASE_URL = "https://api.openai.com"  # Update if your server is running on a different host/port
# MODEL = "gpt-3.5-turbo-instruct"
# API_KEY = "sk-your-openai-api-key"

CHAT_ENDPOINT = f"{BASE_URL}/v1/completions"

print("Running Chat Test with Messages")

# Define the request payload using the "messages" field
payload = {
    "model": MODEL,
    "prompt": ["Tell me something interesting about quantum mechanics."],
    "stream": True,
    "max_tokens": 5,
}
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}",
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
