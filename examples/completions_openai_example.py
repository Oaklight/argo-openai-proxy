import openai

MODEL = "argo:gpt-4o"

client = openai.OpenAI(
    api_key="whatever+random",
    base_url="http://localhost:44500/v1",
)


def chat_test():
    print("Running Chat Test with Messages")

    prompt = ["Tell me something interesting about quantum mechanics."]
    max_tokens = 5

    try:
        response = client.completions.create(
            model=MODEL,
            prompt=prompt,
            max_tokens=max_tokens,
        )
        print("Response:")
        print(response)
    except Exception as e:
        print("Error:", e)


if __name__ == "__main__":
    chat_test()
