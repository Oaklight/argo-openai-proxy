import json
import time
import uuid
import requests
from flask import Flask, jsonify, request
from http import HTTPStatus

app = Flask(__name__)

# Replace this with OpenAI-compatible API URL
ARGO_API_URL = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"


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
        data["user"] = "cels"

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
            return jsonify(
                convert_custom_to_openai_response(
                    response.text, data.get("model", "gpt4o"), int(time.time())
                )
            )
        else:
            return jsonify(response.json())

    except ValueError as err:
        return jsonify({"error": str(err)}), HTTPStatus.BAD_REQUEST
    except requests.HTTPError as err:
        error_message = f"HTTP error occurred: {err}"
        return (
            jsonify({"error": error_message, "details": response.text}),
            response.status_code,
        )
    except requests.RequestException as err:
        error_message = f"Request error occurred: {err}"
        return jsonify({"error": error_message}), HTTPStatus.SERVICE_UNAVAILABLE
    except Exception as err:
        error_message = f"An unexpected error occurred: {err}"
        return jsonify({"error": error_message}), HTTPStatus.INTERNAL_SERVER_ERROR


def convert_custom_to_openai_response(custom_response, model_name, create_timestamp):
    """
    Converts the custom API response to an OpenAI compatible API response.

    :param custom_response: JSON response from the custom API.
    :return: OpenAI compatible JSON response.
    """
    try:
        # Parse the custom response
        custom_response_dict = json.loads(custom_response)

        # Extract the response text
        response_text = custom_response_dict.get("response", "")

        # Construct the OpenAI compatible response
        openai_response = {
            "id": uuid.uuid4(),  # Placeholder ID
            "object": "chat.completion",
            "created": create_timestamp,  # Current timestamp
            "model": model_name,  # Model name
            "choices": [
                {
                    "text": response_text,
                    "index": 0,
                    "finish_reason": "stop",
                    "logprobs": {
                        "tokens": None,
                        "token_logprobs": None,
                        "top_logprobs": None,
                        "text_offset": None,
                    },
                }
            ],
            "usage": {
                "prompt_tokens": 0,  # Placeholder
                "completion_tokens": len(response_text.split()),  # Rough estimate
                "total_tokens": 0,  # Placeholder
            },
        }

        return openai_response

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=6000)
