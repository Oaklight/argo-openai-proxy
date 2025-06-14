import openai

MODEL = "argo:text-embedding-3-small"

client = openai.OpenAI(
    api_key="whatever+random",
    base_url="http://localhost:44498/v1",
)


def embed_test():
    print("Running Embed Test with OpenAI Embeddings")

    input_texts = ["What is your name", "What is your favorite color?"]

    response = client.embeddings.create(model=MODEL, input=input_texts)
    print("Embedding Response:")
    print(response)


if __name__ == "__main__":
    embed_test()
