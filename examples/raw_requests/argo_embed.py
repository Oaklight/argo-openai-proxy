import json

import requests

# API endpoint to POST
# url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/embed/"


BASE_URL = "http://localhost:44500"  # Update if your server is running on a different host/port
EMBED_ENDPOINT = f"{BASE_URL}/v1/embed"
MODEL = "argo:text-embedding-3-small"


def embed_test():
    print("Running Embed Test with Messages")

    payload = {
        "model": MODEL,
        "input": ["What is your name", "What is your favorite color?"],
    }
    headers = {"Content-Type": "application/json"}

    response = requests.post(EMBED_ENDPOINT, headers=headers, json=payload)

    try:
        response.raise_for_status()
        print("Response Status Code:", response.status_code)
        print("Response Body:", json.dumps(response.json(), indent=4))
    except requests.exceptions.HTTPError as err:
        print("HTTP Error:", err)
        print("Response Body:", response.text)
        exit(1)


if __name__ == "__main__":
    embed_test()
