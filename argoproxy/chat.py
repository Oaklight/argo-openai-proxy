import fnmatch
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

from argoproxy.config import config
from argoproxy.utils import make_bar

# Configuration variables
ARGO_API_URL = config["argo_url"]
VERBOSE = config["verbose"]

MODEL_AVAIL = {
    "argo:gpt-3.5-turbo": "gpt35",
    "argo:gpt-3.5-turbo-16k": "gpt35large",
    "argo:gpt-4": "gpt4",
    "argo:gpt-4-32k": "gpt4large",
    "argo:gpt-4-turbo-preview": "gpt4turbo",
    "argo:gpt-4o": "gpt4o",
    "argo:gpt-o1-preview": "gpto1preview",
    "argo:gpt-o1-mini": "gpto1mini",
}

DEFAULT_MODEL = "gpt4o"

NO_SYS_MSG_PATTERNS = {
    "argo:gpt-o1-*",
    "gpto1*",
}

NO_SYS_MSG = [
    model
    for model in MODEL_AVAIL
    if any(fnmatch.fnmatch(model, pattern) for pattern in NO_SYS_MSG_PATTERNS)
] + [
    model
    for model in MODEL_AVAIL.values()
    if any(fnmatch.fnmatch(model, pattern) for pattern in NO_SYS_MSG_PATTERNS)
]


def prepare_request_data(data):
    """
    Prepares the request data by adding the user and remapping the model.
    """
    # Automatically replace or insert the user
    data["user"] = config["user"]

    # Remap the model using MODEL_AVAIL
    if "model" in data:
        user_model = data["model"]
        if user_model in MODEL_AVAIL:
            data["model"] = MODEL_AVAIL[user_model]
        elif user_model in MODEL_AVAIL.values():
            data["model"] = user_model
        else:
            data["model"] = DEFAULT_MODEL
    else:
        data["model"] = DEFAULT_MODEL

    # Convert prompt to list if it's not already
    if "prompt" in data and not isinstance(data["prompt"], list):
        data["prompt"] = [data["prompt"]]

    # Convert system message to user message for specific models
    if data["model"] in NO_SYS_MSG:
        if "messages" in data:
            for message in data["messages"]:
                if message["role"] == "system":
                    message["role"] = "user"
        if "system" in data:
            if isinstance(data["system"], str):
                data["system"] = [data["system"]]
            elif not isinstance(data["system"], list):
                raise ValueError("System prompt must be a string or list")
            data["prompt"] = data["system"] + data["prompt"]
            del data["system"]
            logger.debug(f"New data is {data}")

    return data


async def send_non_streaming_request(session, api_url, data, convert_to_openai):
    """
    Sends a non-streaming request and processes the response.
    """
    headers = {"Content-Type": "application/json"}
    async with session.post(api_url, headers=headers, json=data) as resp:
        response_data = await resp.json()
        resp.raise_for_status()

        if VERBOSE:
            logger.debug(make_bar("[chat] fwd. response"))
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


async def send_streaming_request(
    session, api_url, data, request, convert_to_openai=False
):
    """
    Sends a streaming request and streams the response.

    :param session: The aiohttp ClientSession.
    :param api_url: The API endpoint to send the request to.
    :param data: The JSON data to send in the request.
    :param request: The Sanic request object.
    :param convert_to_openai: Whether to convert the response to OpenAI-compatible format.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "Accept-Encoding": "identity",
    }

    # Set response headers based on the mode
    if convert_to_openai:
        response_headers = {"Content-Type": "text/event-stream"}
    else:
        response_headers = {"Content-Type": "text/plain; charset=utf-8"}

    timeout = aiohttp.ClientTimeout(total=600)  # 10 minutes
    async with session.post(
        api_url, headers=headers, json=data, timeout=timeout
    ) as resp:
        # Initialize the streaming response
        streaming_response = await request.respond(headers=response_headers)

        # Generate a unique ID and timestamp for the completion (if converting to OpenAI format)
        created_timestamp = int(time.time()) if convert_to_openai else None

        # Stream the response chunk by chunk
        async for chunk in resp.content.iter_chunked(1024):
            chunk_text = chunk.decode("utf-8")
            # logger.debug(f"Received chunk: {chunk_text}")

            if convert_to_openai:
                # Convert the chunk to OpenAI-compatible JSON
                chunk_json = convert_custom_to_openai_response(
                    json.dumps({"response": chunk_text}),
                    model_name=data["model"],
                    create_timestamp=created_timestamp,
                    prompt=data.get("prompt", ""),
                    is_streaming=True,
                    finish_reason=None,  # Ongoing chunk
                )
                # Wrap the JSON in SSE format
                sse_chunk = f"data: {json.dumps(chunk_json)}\n\n"
            else:
                # Return the chunk as-is (raw text)
                sse_chunk = chunk_text

            await streaming_response.send(sse_chunk)

        # Handle the final chunk for OpenAI-compatible mode
        if convert_to_openai:
            # Send the [DONE] marker
            sse_done_chunk = "data: [DONE]\n\n"
            await streaming_response.send(sse_done_chunk)

    return None


async def proxy_request(
    convert_to_openai=False, request=None, input_data=None, stream=False
):
    try:
        # Retrieve the incoming JSON data from Sanic request if input_data is not provided
        if input_data is None:
            data = request.json
        else:
            data = input_data

        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        if VERBOSE:
            logger.debug(make_bar("[chat] input"))
            logger.debug(json.dumps(data, indent=4))
            logger.debug(make_bar())

        # Prepare the request data
        data = prepare_request_data(data)

        # Determine the API URL based on whether streaming is enabled
        api_url = config["argo_stream_url"] if stream else config["argo_url"]

        # Forward the modified request to the actual API using aiohttp
        async with aiohttp.ClientSession() as session:
            if stream:
                return await send_streaming_request(
                    session, api_url, data, request, convert_to_openai
                )
            else:
                return await send_non_streaming_request(
                    session, api_url, data, convert_to_openai
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
    custom_response,
    model_name,
    create_timestamp,
    prompt,
    is_streaming=False,
    finish_reason=None,
):
    """
    Converts the custom API response to an OpenAI compatible API response.

    :param custom_response: JSON response from the custom API.
    :param model_name: The model used for the completion.
    :param create_timestamp: Timestamp for the completion.
    :param prompt: The input prompt used in the request.
    :param is_streaming: Whether the response is for streaming mode.
    :param finish_reason: Reason for completion (e.g., "stop" or None).
    :return: OpenAI compatible JSON response.
    """
    try:
        # Parse the custom response
        if isinstance(custom_response, str):
            custom_response_dict = json.loads(custom_response)
        else:
            custom_response_dict = custom_response

        # Extract the response text
        response_text = custom_response_dict.get("response", "")

        if not is_streaming:
            # only count usage if not stream
            # Calculate token counts (simplified example, actual tokenization may differ)
            if isinstance(prompt, list):
                # concatenate the list elements
                prompt = " ".join(prompt)
            prompt_tokens = len(prompt.split())
            completion_tokens = len(response_text.split())
            total_tokens = prompt_tokens + completion_tokens

        # Construct the base OpenAI compatible response
        openai_response = {
            "id": str(uuid.uuid4()),
            "object": "chat.completion.chunk" if is_streaming else "chat.completion",
            "created": create_timestamp,
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "finish_reason": finish_reason,
                    "delta" if is_streaming else "message": {
                        "role": "assistant",
                        "content": response_text,
                    },
                }
            ],
            "system_fingerprint": "",
        }
        if not is_streaming:
            openai_response["usage"] = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
            }
        return openai_response

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}
