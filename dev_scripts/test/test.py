from openai import OpenAI

openai_api_base = f"http://lambda5:44497/v1"

client = OpenAI(
    api_key="random+whatever",
    base_url=openai_api_base,
)

# sampling_params = SamplingParams({"prompt_logprobs": 1, "logprobs": 1))
chat_response = client.chat.completions.create(
    model="argo:gpt-4o",
    messages=[
        {"role": "user", "content": "A detailed description of the biochemical \
            function 5-(hydroxymethyl)furfural/furfural transporter is"},
    ],
    temperature=0.0,
    max_tokens=2056,
)
#print("Chat response:", chat_response)
