import json
import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import yaml
from flask import request, Response

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from argoproxy.utils import make_bar

# Assuming similar config loading and logging setup
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

ARGO_EMBEDDING_API_URL = config["argo_embedding_url"]
VERBOSE = config["verbose"]


# Setup logging
logging.basicConfig(
    level=logging.DEBUG if VERBOSE else logging.INFO, format="%(levelname)s:%(message)s"
)

MODEL_AVAIL = {
    "argo:text-embedding-ada-002": "ada002",
    "argo:text-embedding-3-small": "v3small",
    "argo:text-embedding-3-large": "v3large",
}


def proxy_request():
    try:
        # Retrieve the incoming JSON data
        data = request.get_json(force=True)
        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        if VERBOSE:
            logging.debug(make_bar("[embed] input"))
            logging.debug(json.dumps(data, indent=4))
            logging.debug(make_bar())

            # Remap the model using MODEL_AVAIL
        if "model" in data:
            user_model = data["model"]
            # Check if the user_model is a key in MODEL_AVAIL
            if user_model in MODEL_AVAIL:
                data["model"] = MODEL_AVAIL[user_model]
            # Check if the user_model is a value in MODEL_AVAIL
            elif user_model in MODEL_AVAIL.values():
                data["model"] = user_model
            # If the user_model is not found, set the default model
            else:
                data["model"] = "v3small"
        # If "model" is not provided, set the default model
        else:
            data["model"] = "v3small"

        # Transform the incoming payload to match the destination API format
        data["user"] = config["user"]
        data["prompt"] = data["input"]

        del data["input"]

        headers = {
            "Content-Type": "application/json"
            # Uncomment and customize if needed
            # "Authorization": f"Bearer {YOUR_API_KEY}"
        }

        # Send transformed request to the target API
        response = requests.post(ARGO_EMBEDDING_API_URL, headers=headers, json=data)
        response.raise_for_status()

        if VERBOSE:
            logging.debug(make_bar("[embed] fwd. response"))
            logging.debug(json.dumps(response.json(), indent=4))
            logging.debug(make_bar())

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
