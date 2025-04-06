import json
import os
import sys
from http import HTTPStatus

import aiohttp
from sanic import response
from sanic.log import logger

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from argoproxy.config import config
from argoproxy.constants import EMBED_MODELS as MODEL_AVAIL
from argoproxy.utils import count_tokens, make_bar

ARGO_EMBEDDING_API_URL = config["argo_embedding_url"]
VERBOSE = config["verbose"]


def make_it_openai_embeddings_compat(
    custom_response,
    model_name,
    prompt,
):
    """
    Converts the custom API response to an OpenAI compatible API response.

    :param custom_response: JSON response from the custom API.
    :param model_name: The model used for the completion.
    :param prompt: The input prompt used in the request.
    :return: OpenAI compatible JSON response.
    """
    try:
        # Parse the custom response
        if isinstance(custom_response, str):
            custom_response_dict = json.loads(custom_response)
        else:
            custom_response_dict = custom_response

        # Calculate token counts
        if isinstance(prompt, str):
            prompt_tokens = count_tokens(prompt, model_name)
        else:
            prompt_tokens = sum(count_tokens(text, model_name) for text in prompt)

        # Construct the OpenAI compatible response
        data = []
        for embedding in custom_response_dict["embedding"]:
            data.append(
                {
                    "object": "embedding",
                    "index": 0,
                    "embedding": embedding,
                }
            )
        openai_response = {
            "object": "list",
            "data": data,
            "model": model_name,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "total_tokens": prompt_tokens,
            },
        }
        return openai_response

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}


async def proxy_request(request, convert_to_openai=False):
    try:
        # Retrieve the incoming JSON data
        data = request.json
        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        if VERBOSE:
            logger.debug(make_bar("[embed] input"))
            logger.debug(json.dumps(data, indent=4))
            logger.debug(make_bar())

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
        data["prompt"] = (
            [data["input"]] if not isinstance(data["input"], list) else data["input"]
        )

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
                    logger.debug(make_bar("[embed] fwd. response"))
                    logger.debug(json.dumps(response_data, indent=4))
                    logger.debug(make_bar())

                if convert_to_openai:
                    openai_response = make_it_openai_embeddings_compat(
                        json.dumps(response_data),
                        data["model"],
                        data["prompt"],
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
