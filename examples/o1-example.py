import argparse
import json

import requests


def main():
    # API endpoint URL (adjust the port if necessary)
    # url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
    url = "http://localhost:44498/v1/chat"

    # Headers
    headers = {"Content-Type": "application/json"}

    # System prompt, will be converted to user message for gpt-o1 series
    system_prompt = (
        "You are a super smart and helpful AI. You always answer truthfully and provide "
        "the answer directly if you can. If you can't answer because you don't know the "
        "answer you say I don't know or you provide help in rephrasing the question. "
        "You do not give meta answers."
    )

    # Data payload template
    data_template = {
        "user": "cels",
        "model": "argo:gpt-o1-mini",
        "system": system_prompt,
        "prompt": [],  # Will be updated with the user's message
        "stop": [],
        "temperature": 0.0,
        "top_p": 1.0,
        "max_tokens": 2056,
    }

    # The user's message
    user_message = (
        "Please generate four hypotheses on the origins of life that could be explored with a "
        "self-driving laboratory. For each example please list the key equipment and instruments "
        "that would be needed and the experimental protocols that would need to be automated to "
        "test the hypotheses."
    )

    # Update the data payload with the user's message
    data = data_template.copy()
    data["prompt"] = [user_message]

    # Send the POST request to the API
    response = requests.post(url, headers=headers, json=data)

    try:
        response.raise_for_status()
        print(response.text)

    except requests.exceptions.HTTPError as err:
        print(err)
        print(response.text)
        exit(1)


if __name__ == "__main__":
    main()
