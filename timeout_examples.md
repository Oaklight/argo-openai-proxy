### Timeout Override Examples

To override the default timeout setting defined in `config.yaml`, use the examples below with different tools and libraries. **Note:** Make sure to replace `http://localhost:44497` with your actual Argo Proxy URL.

#### cURL

Specify a timeout directly within your cURL command using `--max-time`.

```bash
curl --max-time 120 -X POST "http://your-argo-proxy-url/v1/chat/completions" -H "Content-Type: application/json" --data '{"model":"argo:gpt-3.5-turbo","messages":[{"role":"user","content":"Hello!"}]}'
```

#### OpenAI Python Client Style

When using the OpenAI client, pass the timeout as an additional parameter.

```python file.py
import openai

openai.api_base = "http://your-argo-proxy-url/v1"
response = openai.ChatCompletion.create(
    model="argo:gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Hello!"}],
    timeout=120
)
print(response)
```

#### Requests Library Style

Use the `timeout` parameter in the requests library.

```python file.py
import requests

url = "http://your-argo-proxy-url/v1/chat/completions"
payload = {"model": "argo:gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}
response = requests.post(url, json=payload, timeout=120)
print(response.json())
```

#### HTTPX Library Style

HTTPX supports async requests, and you can set a timeout using the `timeout` parameter.

```python file.py
import httpx

url = "http://your-argo-proxy-url/v1/chat/completions"
payload = {"model": "argo:gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}

with httpx.Client(timeout=120) as client:
    response = client.post(url, json=payload)
    print(response.json())
```

#### Aiohttp Style

For async requests with Aiohttp, use a `ClientTimeout` object.

```python file.py
import aiohttp
import asyncio

async def fetch():
    url = "http://your-argo-proxy-url/v1/chat/completions"
    payload = {"model": "argo:gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello!"}]}
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as response:
            data = await response.json()
            print(data)

asyncio.run(fetch())
```

In each of these examples, replace `http://your-argo-proxy-url` with the actual URL where your Argo Proxy instance is hosted. This ensures all your requests reach the intended endpoint.
