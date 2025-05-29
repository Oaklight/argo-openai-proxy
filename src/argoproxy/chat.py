import fnmatch
import json
import time
import uuid
from http import HTTPStatus
from typing import Any, Callable, Dict, Optional

import aiohttp
from sanic import response
from sanic.log import logger
from sanic.response import HTTPResponse

from .constants import CHAT_MODELS

from .utils import (
    calculate_prompt_tokens,
    count_tokens,
    make_bar,
    resolve_model_name,
)

DEFAULT_MODEL = "gpt4o"

NO_SYS_MSG_PATTERNS = {
    "^argo:gpt-o.*$",
    "^argo:o.*$",
    "^gpto.*$",
}

NO_SYS_MSG = [
    model
    for model in CHAT_MODELS
    if any(fnmatch.fnmatch(model, pattern) for pattern in NO_SYS_MSG_PATTERNS)
]

DEFAULT_TIMEOUT_SECONDS = 600


def make_it_openai_chat_completions_compat(
    custom_response,
    model_name,
    create_timestamp,
    prompt_tokens,
    is_streaming=False,
    finish_reason=None,
):
    """
    Converts the custom API response to an OpenAI compatible API response.

    :param custom_response: JSON response from the custom API.
    :param model_name: The model used for the completion.
    :param create_timestamp: Timestamp for the completion.
    :param prompt_tokens: The input prompt token count used in the request.
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
            completion_tokens = count_tokens(response_text, model_name)
            total_tokens = prompt_tokens + completion_tokens

        # Construct the base OpenAI compatible response
        openai_response = {
            "id": str(uuid.uuid4().hex),
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


def prepare_request_data(data, request):
    """
    Prepares the request data by adding the user and remapping the model.
    """
    config = request.app.ctx.config
    # Automatically replace or insert the user
    data["user"] = config.user

    # Remap the model using MODEL_AVAIL
    if "model" in data:
        data["model"] = resolve_model_name(
            data["model"], DEFAULT_MODEL, avail_models=CHAT_MODELS
        )
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
            if config.verbose:
                logger.info(f"New data is {data}")

    return data


async def send_non_streaming_request(
    session: aiohttp.ClientSession,
    api_url: str,
    data: Dict[str, Any],
    convert_to_openai: bool = False,
    openai_compat_fn: Callable = make_it_openai_chat_completions_compat,
    timeout: Optional[aiohttp.ClientTimeout] = None,
) -> HTTPResponse:
    """
    Sends a non-streaming request to the specified API URL and processes the response.

    :param session: The aiohttp ClientSession used to send the request.
    :param api_url: The URL of the API endpoint to which the request is sent.
    :param data: The JSON data to be sent in the request body.
    :param convert_to_openai: A boolean flag indicating whether to convert the response to OpenAI-compatible format. Defaults to False.
    :param openai_compat_fn: The function used to convert the response to OpenAI-compatible format. Defaults to `make_it_openai_chat_completions_compat`.
    :param timeout: Optional timeout in seconds for the request. If not provided, the default timeout from the configuration is used.

    :return: A Sanic response object containing the JSON response from the API, with the appropriate status code and content type.
    """
    headers = {"Content-Type": "application/json"}
    async with session.post(
        api_url, headers=headers, json=data, timeout=timeout
    ) as resp:
        response_data = await resp.json()
        resp.raise_for_status()

        if convert_to_openai:
            # Calculate prompt tokens using the unified function
            prompt_tokens = calculate_prompt_tokens(data, data["model"])
            openai_response = openai_compat_fn(
                json.dumps(response_data),
                model_name=data.get("model"),
                create_timestamp=int(time.time()),
                prompt_tokens=prompt_tokens,
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
    session: aiohttp.ClientSession,
    api_url: str,
    data: Dict[str, Any],
    request: Any,
    convert_to_openai: bool = False,
    openai_compat_fn: Callable = make_it_openai_chat_completions_compat,
    timeout: Optional[aiohttp.ClientTimeout] = None,
) -> None:
    """
    Sends a streaming request to the specified API URL and streams the response back to the client.

    :param session: The aiohttp ClientSession used to send the request.
    :param api_url: The URL of the API endpoint to which the request is sent.
    :param data: The JSON data to be sent in the request body.
    :param request: The Sanic request object used to handle the streaming response.
    :param convert_to_openai: A boolean flag indicating whether to convert the response to OpenAI-compatible format. Defaults to False.
    :param openai_compat_fn: The function used to convert the response to OpenAI-compatible format. Defaults to `make_it_openai_chat_completions_compat`.
    :param timeout: Optional timeout in seconds for the request. If not provided, the default timeout from the configuration is used.

    :return: None, as the response is streamed back to the client in chunks.
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
                # Calculate prompt tokens using the unified function
                prompt_tokens = calculate_prompt_tokens(data, data["model"])
                # Convert the chunk to OpenAI-compatible JSON
                chunk_json = openai_compat_fn(
                    json.dumps({"response": chunk_text}),
                    model_name=data["model"],
                    create_timestamp=created_timestamp,
                    prompt_tokens=prompt_tokens,
                    is_streaming=True,
                    finish_reason=None,  # Ongoing chunk
                )
                # Wrap the JSON in SSE format
                sse_chunk = f"data: {json.dumps(chunk_json)}\n\n"
            else:
                # Return the chunk as-is (raw text)
                sse_chunk = chunk_text

            # logger.debug(f"sse_chunk is {sse_chunk}")
            await streaming_response.send(sse_chunk)

        # Handle the final chunk for OpenAI-compatible mode
        if convert_to_openai:
            # Send the [DONE] marker
            sse_done_chunk = "data: [DONE]\n\n"
            await streaming_response.send(sse_done_chunk)

    return None


async def proxy_request(
    convert_to_openai=False, request=None, input_data=None, stream=False, timeout=None
):
    """
    Proxies the request to the upstream API, handling both streaming and non-streaming modes.

    :param convert_to_openai: Whether to convert the response to OpenAI-compatible format.
    :param request: The Sanic request object.
    :param input_data: Optional input data (used for testing).
    :param stream: Whether to enable streaming mode.
    :param timeout: Optional timeout in seconds for the request
    :return: The response from the upstream API.
    """
    config = request.app.ctx.config

    try:
        # Retrieve the incoming JSON data from Sanic request if input_data is not provided
        if input_data is None:
            data = request.json
        else:
            data = input_data

        if not data:
            raise ValueError("Invalid input. Expected JSON data.")
        if config.verbose:
            logger.info(make_bar("[chat] input"))
            logger.info(json.dumps(data, indent=4))
            logger.info(make_bar())

        # Prepare the request data
        data = prepare_request_data(data, request)

        # Determine the API URL based on whether streaming is enabled
        api_url = config.argo_stream_url if stream else config.argo_url

        if timeout:
            # Use provided timeout or default from config
            timeout = aiohttp.ClientTimeout(total=timeout)
        else:
            timeout = aiohttp.ClientTimeout(
                total=config.timeout or DEFAULT_TIMEOUT_SECONDS
            )

        # Forward the modified request to the actual API using aiohttp
        async with aiohttp.ClientSession() as session:
            if stream:
                return await send_streaming_request(
                    session,
                    api_url,
                    data,
                    request,
                    convert_to_openai,
                    timeout=timeout,
                )
            else:
                return await send_non_streaming_request(
                    session,
                    api_url,
                    data,
                    convert_to_openai,
                    timeout=timeout,
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
