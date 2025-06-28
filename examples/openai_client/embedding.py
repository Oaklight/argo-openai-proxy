import os

import openai

MODEL = "argo:text-embedding-3-small"
BASE_URL = os.getenv("BASE_URL", "http://localhost:44498")
API_KEY = os.getenv("API_KEY", "whatever+random")

client = openai.OpenAI(
    api_key=API_KEY,
    base_url=BASE_URL,
)


def embed_test():
    print("Running Embed Test with OpenAI Embeddings")

    input_texts = ["What is your name", "What is your favorite color?"]

    response = client.embeddings.create(model=MODEL, input=input_texts)
    print("Embedding Response:")
    print(response)


if __name__ == "__main__":
    embed_test()
