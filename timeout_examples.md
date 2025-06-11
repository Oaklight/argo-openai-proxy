# Timeout Override Examples

To override the default timeout setting defined in `config.yaml`, use the examples below with different tools and libraries. **Note:** Make sure to replace `http://your-argo-proxy-url` with your actual Argo Proxy URL, such as `http://localhost:44498` or `lambda5:44497`.

This timeout is a client-side configuration and does not affect the server. The server will keep the connection open until it finishes or client disconnects.

## cURL

Specify a timeout directly within your cURL command using `--max-time`.

```bash
curl --max-time 120 -X POST "http://your-argo-proxy-url/v1/chat/completions" -H "Content-Type: application/json" --data '{"model":"argo:gpt-o1-preview","messages":[{"role":"user","content":"Draft a strategic roadmap for building an integrated smart city that leverages autonomous public transportation, renewable energy, IoT-driven urban management, resilient disaster response, and sustainable resource utilization."}]}'
```

## OpenAI Python Client Style

When using the OpenAI client, pass the timeout as an additional parameter.
Note: OpenAI client by default will retry on failure for 3 times.

```python
from openai import OpenAI

client = OpenAI(api_key="your_api_key", base_url="http://your-argo-proxy-url/v1")
response = client.chat.completions.create(
    model="argo:gpt-o1-preview",
    messages=[{"role": "user", "content": "Draft a strategic roadmap for building an integrated smart city that leverages autonomous public transportation, renewable energy, IoT-driven urban management, resilient disaster response, and sustainable resource utilization."}],
    timeout=120
)
print(response)
```

## Requests Library Style

Use the `timeout` parameter in the requests library.

```python
import requests

url = "http://your-argo-proxy-url/v1/chat/completions"
payload = {"model": "argo:gpt-o1-preview", "messages": [{"role": "user", "content": "Draft a strategic roadmap for building an integrated smart city that leverages autonomous public transportation, renewable energy, IoT-driven urban management, resilient disaster response, and sustainable resource utilization."}]}
response = requests.post(url, json=payload, timeout=120)
print(response.json())
```

## HTTPX Library Style

HTTPX supports async requests, and you can set a timeout using the `timeout` parameter.

```python
import httpx

url = "http://your-argo-proxy-url/v1/chat/completions"
payload = {"model": "argo:gpt-o1-preview", "messages": [{"role": "user", "content": "Draft a strategic roadmap for building an integrated smart city that leverages autonomous public transportation, renewable energy, IoT-driven urban management, resilient disaster response, and sustainable resource utilization."}]}

with httpx.Client(timeout=120) as client:
    response = client.post(url, json=payload)
    print(response.json())
```

## Aiohttp Style

For async requests with Aiohttp, use a `ClientTimeout` object.

```python
import aiohttp
import asyncio

async def fetch():
    url = "http://your-argo-proxy-url/v1/chat/completions"
    payload = {"model": "argo:gpt-o1-preview", "messages": [{"role": "user", "content": "Draft a strategic roadmap for building an integrated smart city that leverages autonomous public transportation, renewable energy, IoT-driven urban management, resilient disaster response, and sustainable resource utilization."}]}
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            data = await response.json()
            print(data)

asyncio.run(fetch())
```

In each of these examples, replace `http://your-argo-proxy-url` with the actual URL where your Argo Proxy instance is hosted. This ensures all your requests reach the intended endpoint.
