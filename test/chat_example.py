import requests
import json

# Configuration
BASE_URL = (
    "http://localhost:5000"  # Update if your server is running on a different host/port
)
CHAT_ENDPOINT = f"{BASE_URL}/v1/chat/completions"
MODEL = "argo:gpt-4o"


# Test Case: Successful Chat Request with Messages
def chat_test():
    print("Running Chat Test with Messages")

    # Define the request payload using the "messages" field
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "Hello, how are you?"}],
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
