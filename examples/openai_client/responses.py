import openai
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file if n

MODEL = os.getenv("MODEL", "argo:gpt-4o")  # Default to "ar"argo:gpt-4o"

client = openai.OpenAI(
    api_key=os.getenv("API_KEY", "whatever+random"),
    base_url=os.getenv("BASE_URL", "http://localhost:44500/v1"),
)


def stream_chat_test():
    print("Running Chat Test with Streaming")

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": "Tell me something interesting about quantum mechanics.",
        },
    ]
    max_tokens = 5

    try:
        response = client.responses.create(
            model=MODEL,
            instructions="Talk like a pirate.",
            input=messages,
            max_output_tokens=max_tokens,
        )
        print("Streaming Response:")
        print(response)
    except Exception as e:
        print("\nError:", e)


if __name__ == "__main__":
    stream_chat_test()
