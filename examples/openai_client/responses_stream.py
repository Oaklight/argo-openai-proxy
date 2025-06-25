import os

import openai
from dotenv import load_dotenv

load_dotenv()

MODEL = os.getenv("MODEL", "argo:gpt-4o")
BASE_URL = os.getenv("BASE_URL", "http://localhost:44498")

client = openai.OpenAI(
    api_key="whatever+random",
    base_url=f"{BASE_URL}/v1",
)


def stream_chat_test():
    print("Running Chat Test with Streaming")

    messages = [
        {
            "role": "user",
            "content": "Tell me something interesting about quantum mechanics.",
        },
    ]

    try:
        response = client.responses.create(model=MODEL, input=messages, stream=True)
        print("Streaming Response:")
        for event in response:
            if event.type == "response.output_text.delta":
                print(event.delta, end="", flush=True)
            # else:
            #     print(event)
    except Exception as e:
        print("\nError:", e)


if __name__ == "__main__":
    stream_chat_test()
