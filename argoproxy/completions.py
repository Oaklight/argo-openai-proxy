import json
import os
import sys
import time
import uuid
from http import HTTPStatus

import aiohttp
from sanic import response
from sanic.log import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from argoproxy.chat import DEFAULT_MODEL, MODEL_AVAIL, NO_SYS_MSG
from argoproxy.config import config
from argoproxy.utils import make_bar

# Configuration variables
ARGO_API_URL = config["argo_url"]
VERBOSE = config["verbose"]

async def proxy_request(convert_to_openai=False, request=None, input_data=None):
    try:
        # Retrieve the incoming JSON data from Sanic request if input_data is not provided
        if input_data is None:
            data = request.json
        else:
            data = input_data

        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        if VERBOSE:
            logger.debug(make_bar("[completion] input"))
            logger.debug(json.dumps(data, indent=4))
            logger.debug(make_bar())

        # Automatically replace or insert the user
        data["user"] = config["user"]

        # Remap the model using MODEL_AVAIL
        if "model" in data:
            user_model = data["model"]
            # Check if the user_model is a key in MODEL_AVAIL
            if user_model in MODEL_AVAIL:
                data["model"] = MODEL_AVAIL[user_model]
            # Check if the user_model is a value in MODEL_AVAIL
            elif user_model in MODEL_AVAIL.values():
                data["model"] = user_model
            # If the user_model is not found, set the default model to GPT-4o
            else:
                data["model"] = DEFAULT_MODEL
        # If the model argument is missing, set the default model to GPT-4o
        else:
            data["model"] = DEFAULT_MODEL

        if "prompt" in data:
            if not isinstance(data["prompt"], list):
                tmp = data["prompt"]
                data["prompt"] = [tmp]

        if data["model"] in NO_SYS_MSG:
            if "system" in data:
                # check if system is str or list, make it list
                if isinstance(data["system"], str):
                    data["system"] = [data["system"]]
                elif not isinstance(data["system"], list):
                    raise ValueError("System prompt must be a string or list")
                # convert system prompt to prompt
                data["prompt"] = data["system"] + data["prompt"]
                del data["system"]
                logger.debug(f"new data is {data}")

        headers = {
            "Content-Type": "application/json"
            # Uncomment and customize if needed
            # "Authorization": f"Bearer {YOUR_API_KEY}"
        }

        # Forward the modified request to the actual API using aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(ARGO_API_URL, headers=headers, json=data) as resp:
                response_data = await resp.json()
                resp.raise_for_status()

                if VERBOSE:
                    logger.debug(make_bar("[completion] fwd. response"))
                    logger.debug(json.dumps(response_data, indent=4))
                    logger.debug(make_bar())

                if convert_to_openai:
                    openai_response = convert_custom_to_openai_response(
                        json.dumps(response_data),
                        data.get("model"),
                        int(time.time()),
                        data.get("prompt", ""),
                    )
                    return response.json(
                        openai_response,
                        status=resp.status,
                        content_type="application/json",
                    )
                else:
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
