import json
import logging
import os
import sys
from http import HTTPStatus

import aiohttp
from sanic import response

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from argoproxy.config import config
from argoproxy.utils import make_bar

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


async def proxy_request(request):
    try:
        # Retrieve the incoming JSON data
        data = request.json
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

        # Send transformed request to the target API using aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(
                ARGO_EMBEDDING_API_URL, headers=headers, json=data
            ) as resp:
                response_data = await resp.json()
                resp.raise_for_status()

                if VERBOSE:
                    logging.debug(make_bar("[embed] fwd. response"))
                    logging.debug(json.dumps(response_data, indent=4))
                    logging.debug(make_bar())

                return response.json(
                    response_data,
                    status=resp.status,
                    content_type="application/json",
                )

    except ValueError as err:
        return response.json(
            {"error": str(err)},
            status=HTTPStatus.BAD_REQUEST,
            content_type="application/json",
        )
    except aiohttp.ClientError as err:
        error_message = f"HTTP error occurred: {err}"
        return response.json(
            {"error": error_message},
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            content_type="application/json",
        )
    except Exception as err:
        error_message = f"An unexpected error occurred: {err}"
        return response.json(
            {"error": error_message},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )
