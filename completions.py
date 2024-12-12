import json
import logging
import os
import sys
import time
import uuid
from http import HTTPStatus

import requests
import yaml
from flask import Response, request

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from utils import make_bar

with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Configuration variables
ARGO_API_URL = config["argo_url"]
VERBOSE = config["verbose"]

# Setup logging
logging.basicConfig(
    level=logging.DEBUG if VERBOSE else logging.INFO, format="%(levelname)s:%(message)s"
)


def proxy_request(convert_to_openai=False):
    try:
        # Retrieve the incoming JSON data
        data = request.get_json(force=True)
        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        if VERBOSE:
            logging.debug(make_bar("[completion] input"))
            logging.debug(json.dumps(data, indent=4))
            logging.debug(make_bar())

        # Automatically replace or insert the user
        data["user"] = config["user"]

        if "prompt" in data.keys():
            if not isinstance(data["prompt"], list):
                tmp = data["prompt"]
                data["prompt"] = [tmp]

        headers = {
            "Content-Type": "application/json"
            # Uncomment and customize if needed
            # "Authorization": f"Bearer {YOUR_API_KEY}"
        }

        # Forward the modified request to the actual API
        response = requests.post(ARGO_API_URL, headers=headers, json=data)
        response.raise_for_status()

        if VERBOSE:
            logging.debug(make_bar("[completion] fwd. response"))
            logging.debug(json.dumps(response.json(), indent=4))
            logging.debug(make_bar())

        if convert_to_openai:
            openai_response = convert_custom_to_openai_response(
                response.text,
                data.get("model", "gpto1preview"),
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
    Converts the custom API response to an OpenAI compatible completion API response.

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
        if isinstance(prompt, list):
            # concatenate the list elements
            prompt = " ".join(prompt)
        prompt_tokens = len(prompt.split())
        completion_tokens = len(response_text.split())
        total_tokens = prompt_tokens + completion_tokens

        # Construct the OpenAI compatible response
        openai_response = {
            "id": f"cmpl-{uuid.uuid4().hex}",  # Unique ID
            "object": "text_completion",  # Object type
            "created": create_timestamp,  # Current timestamp
            "model": model_name,  # Model name
            "choices": [
                {
                    "text": response_text,
                    "index": 0,
                    "logprobs": None,
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": prompt_tokens,  # Actual value based on prompt
                "completion_tokens": completion_tokens,  # Actual value based on response
                "total_tokens": total_tokens,  # Sum of prompt and completion tokens
            },
        }

        return openai_response

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}
