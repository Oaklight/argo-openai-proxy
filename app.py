import yaml
import json
import time
import uuid
import requests
from flask import Flask, request, Response
from http import HTTPStatus

app = Flask(__name__)

# Read configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Replace this with the URL from the configuration
ARGO_API_URL = config["argo_url"]


@app.route("/v1/chat", methods=["POST"])
def proxy_chat_request():
    return proxy_request(convert_to_openai=False)


@app.route("/v1/chat/completions", methods=["POST"])
@app.route("/v1/completions", methods=["POST"])
def proxy_openai_compatible_request():
    return proxy_request(convert_to_openai=True)


def proxy_request(convert_to_openai=False):
    try:
        # Retrieve the incoming JSON data
        data = request.get_json(force=True)
        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        print("-" * 25, "input", "-" * 25)
        print(json.dumps(data, indent=4))
        print("-" * 50)

        # Automatically replace or insert the user
        data["user"] = config["user"]

        headers = {
            "Content-Type": "application/json"
            # Uncomment and customize if needed
            # "Authorization": f"Bearer {YOUR_API_KEY}"
        }

        # Forward the modified request to the actual API
        response = requests.post(ARGO_API_URL, headers=headers, json=data)
        response.raise_for_status()

        print("-" * 25, "forwarded response", "-" * 25)
        print(json.dumps(response.json(), indent=4))
        print("-" * 50)

        if convert_to_openai:
            openai_response = convert_custom_to_openai_response(
                response.text,
                data.get("model", "gpt4o"),
                int(time.time()),
                data.get("prompt", ""),
            )
            return Response(
                json.dumps(openai_response),
                status=response.status_code,
                content_type="application/json",
            )
        else:
            return Response(
                response.text,
                status=response.status_code,
                content_type="application/json",
            )

    except ValueError as err:
        return Response(
            json.dumps({"error": str(err)}),
            status=HTTPStatus.BAD_REQUEST,
            content_type="application/json",
        )
    except requests.HTTPError as err:
        error_message = f"HTTP error occurred: {err}"
        return Response(
            json.dumps({"error": error_message, "details": response.text}),
            status=response.status_code,
            content_type="application/json",
        )
    except requests.RequestException as err:
        error_message = f"Request error occurred: {err}"
        return Response(
            json.dumps({"error": error_message}),
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            content_type="application/json",
        )
    except Exception as err:
        error_message = f"An unexpected error occurred: {err}"
        return Response(
            json.dumps({"error": error_message}),
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )


def convert_custom_to_openai_response(
    custom_response, model_name, create_timestamp, prompt
):
    """
    Converts the custom API response to an OpenAI compatible API response.

    :param custom_response: JSON response from the custom API.
    :param prompt: The input prompt used in the request.
    :return: OpenAI compatible JSON response.
    """
    try:
        # Parse the custom response
        custom_response_dict = json.loads(custom_response)

        # Extract the response text
        response_text = custom_response_dict.get("response", "")

        # Calculate token counts (simplified example, actual tokenization may differ)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(response_text.split())
        total_tokens = prompt_tokens + completion_tokens

        # Construct the OpenAI compatible response
        openai_response = {
            "id": str(uuid.uuid4()),  # Unique ID
            "object": "chat.completion",  # Object type
            "created": create_timestamp,  # Current timestamp
            "model": model_name,  # Model name
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,  # Actual value based on prompt
                "completion_tokens": completion_tokens,  # Actual value based on response
                "total_tokens": total_tokens,  # Sum of prompt and completion tokens
            },
            "system_fingerprint": "",  # Include system fingerprint as an empty string
        }

        return openai_response

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config["port"])
