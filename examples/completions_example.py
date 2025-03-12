import json

import requests

# Configuration
BASE_URL = "http://localhost:44498"  # Update if your server is running on a different host/port
CHAT_ENDPOINT = f"{BASE_URL}/v1/completions"
MODEL = "argo:gpt-o1-mini"

system_prompt = (
    "You are a super smart and helpful AI. You always answer truthfully and provide "
    "the answer directly if you can. If you can't answer because you don't know the "
    "answer you say I don't know or you provide help in rephrasing the question. "
    "You do not give meta answers."
)
user_message = (
    "Please generate four hypotheses on the origins of life that could be explored with a "
    "self-driving laboratory. For each example please list the key equipment and instruments "
    "that would be needed and the experimental protocols that would need to be automated to "
    "test the hypotheses."
)


# Test Case: Successful Chat Request with Messages
def chat_test():
    print("Running Chat Test with Messages")

    # Define the request payload using the "messages" field
    payload = {
        "model": MODEL,
        "system": system_prompt,
        "prompt": user_message,
        "user": "test_user",  # This will be overridden by the proxy_request function
    }
    headers = {"Content-Type": "application/json"}

    # Send the POST request
    response = requests.post(CHAT_ENDPOINT, headers=headers, json=payload)

    try:
        response.raise_for_status()
        print("Response Status Code:", response.status_code)
        print("Response Body:", json.dumps(response.json(), indent=4))
    except requests.exceptions.HTTPError as err:
        print("HTTP Error:", err)
        print("Response Body:", response.text)
        exit(1)


# Run the test
if __name__ == "__main__":
    chat_test()
