import fnmatch
import json
import time
import uuid
from http import HTTPStatus
from typing import Any, Callable, Dict

import aiohttp
from aiohttp import web
from loguru import logger

from .config import ArgoConfig
from .constants import CHAT_MODELS
from .types import ChatCompletion, CompletionUsage
from .types.chat_completion import (
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChoiceDelta,
    NonStreamChoice,
    StreamChoice,
)
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
            usage = CompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            ).model_dump()

        if is_streaming:
            openai_response = ChatCompletionChunk(
                id=str(uuid.uuid4().hex),
                created=create_timestamp,
                model=model_name,
                choices=[
                    StreamChoice(
                        index=0,
                        delta=ChoiceDelta(
                            content=response_text,
                        ),
                        finish_reason=finish_reason or "stop",
                    )
                ],
            ).model_dump()
        else:
            openai_response = ChatCompletion(
                id=str(uuid.uuid4().hex),
                created=create_timestamp,
                model=model_name,
                choices=[
                    NonStreamChoice(
                        index=0,
                        message=ChatCompletionMessage(
                            content=response_text,
                        ),
                        finish_reason=finish_reason or "stop",
                    )
                ],
                usage=usage,
            ).model_dump()

        return openai_response

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}


def prepare_request_data(data, request: web.Request):
    """
    Prepares the request data by adding the user and remapping the model.
    """
    config: ArgoConfig = request.app["config"]
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
) -> web.Response:
    """Sends a non-streaming request to the specified API URL and processes the response.

    Args:
        session: The aiohttp ClientSession used to send the request.
        api_url: The URL of the API endpoint to which the request is sent.
        data: The JSON data to be sent in the request body.
        convert_to_openai: Whether to convert the response to OpenAI-compatible format.
            Defaults to False.
        openai_compat_fn: Function to convert response to OpenAI-compatible format.
            Defaults to `make_it_openai_chat_completions_compat`.

    Returns:
        A web.Response object containing the JSON response from the API with appropriate
        status code and content type.

    Raises:
        aiohttp.ClientError: If the request fails.
    """
    headers = {"Content-Type": "application/json"}
    async with session.post(api_url, headers=headers, json=data) as upstream_resp:
        response_data = await upstream_resp.json()
        upstream_resp.raise_for_status()

        if convert_to_openai:
            # Calculate prompt tokens using the unified function
            prompt_tokens = calculate_prompt_tokens(data, data["model"])
            openai_response = openai_compat_fn(
                json.dumps(response_data),
                model_name=data.get("model"),
                create_timestamp=int(time.time()),
                prompt_tokens=prompt_tokens,
            )
            return web.json_response(
                openai_response,
                status=upstream_resp.status,
                content_type="application/json",
            )
        else:
            return web.json_response(
                response_data,
                status=upstream_resp.status,
                content_type="application/json",
            )


async def send_streaming_request(
    session: aiohttp.ClientSession,
    api_url: str,
    data: Dict[str, Any],
    request: Any,
    convert_to_openai: bool = False,
    openai_compat_fn: Callable = make_it_openai_chat_completions_compat,
) -> None:
    """Sends a streaming request to the specified API URL and streams the response back to the client.

    Args:
        session: The aiohttp ClientSession used to send the request.
        api_url: The URL of the API endpoint to which the request is sent.
        data: The JSON payload to send in the request body.
        request: The web request object used to stream the response back to the client.
        convert_to_openai: Whether to convert the response into OpenAI-compatible format.
            Defaults to False.
        openai_compat_fn: Function to convert response into OpenAI-compatible format.
            Defaults to `make_it_openai_chat_completions_compat`.

    Returns:
        None. The streaming response is sent back to the client in chunks.

    Raises:
        aiohttp.ClientError: If the request fails.
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "Accept-Encoding": "identity",
    }

    # Set response headers based on the mode
    if convert_to_openai:
        response_headers = {"Content-Type": "text/event-stream"}
        created_timestamp = int(time.time())
        prompt_tokens = calculate_prompt_tokens(data, data["model"])
    else:
        response_headers = {"Content-Type": "text/plain; charset=utf-8"}

    async with session.post(api_url, headers=headers, json=data) as upstream_resp:
        # Initialize the streaming response
        response_headers.update(
            {
                k: v
                for k, v in upstream_resp.headers.items()
                if k.lower()
                not in ("Content-Type", "content-encoding", "transfer-encoding")
            }
        )
        response = web.StreamResponse(
            status=upstream_resp.status,
            headers=response_headers,
        )
        response.enable_chunked_encoding()
        await response.prepare(request)

        # Stream the response chunk by chunk
        async for chunk in upstream_resp.content.iter_any():
            if convert_to_openai:
                # Convert the chunk to OpenAI-compatible JSON
                chunk_json = openai_compat_fn(
                    json.dumps({"response": chunk.decode()}),
                    model_name=data["model"],
                    create_timestamp=created_timestamp,
                    prompt_tokens=prompt_tokens,
                    is_streaming=True,
                    finish_reason=None,  # Ongoing chunk
                )
                # Wrap the JSON in SSE format
                sse_chunk = f"data: {json.dumps(chunk_json)}\n\n"
                await response.write(sse_chunk.encode())
            else:
                # Return the chunk as-is (raw text)
                await response.write(chunk)

        # Handle the final chunk for OpenAI-compatible mode
        if convert_to_openai:
            # Send the [DONE] marker
            sse_done_chunk = "data: [DONE]\n\n"
            await response.write(sse_done_chunk.encode())

        # Ensure response is properly closed
        await response.write_eof()

        return response


async def proxy_request(request: web.Request, *, convert_to_openai=False):
    """Proxies the request to the upstream API, handling both streaming and non-streaming modes.

    Args:
        convert_to_openai: Whether to convert the response to OpenAI-compatible format.
            Defaults to False.
        request: The web request object containing incoming request data.
        input_data: Optional input data (used for testing). If None, the request JSON
            data will be used.
        stream: Whether to enable streaming mode. Defaults to False.

    Returns:
        A web.Response object from the upstream API.

    Raises:
        ValueError: If the input data is invalid or missing.
        aiohttp.ClientError: If the HTTP request fails.
        Exception: For unexpected server or runtime errors.
    """
    config: ArgoConfig = request.app["config"]

    try:
        # Retrieve the incoming JSON data from request if input_data is not provided

        data = await request.json()
        stream = data.get("stream", False)

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

        # Forward the modified request to the actual API using aiohttp
        async with aiohttp.ClientSession() as session:
            if stream:
                return await send_streaming_request(
                    session,
                    api_url,
                    data,
                    request,
                    convert_to_openai,
                )
            else:
                return await send_non_streaming_request(
                    session,
                    api_url,
                    data,
                    convert_to_openai,
                )

    except ValueError as err:
        return web.json_response(
            {"error": str(err)},
            status=HTTPStatus.BAD_REQUEST,
            content_type="application/json",
        )
    except aiohttp.ClientError as err:
        error_message = f"HTTP error occurred: {err}"
        return web.json_response(
            {"error": error_message},
            status=HTTPStatus.SERVICE_UNAVAILABLE,
            content_type="application/json",
        )
    except Exception as err:
        error_message = f"An unexpected error occurred: {err}"
        return web.json_response(
            {"error": error_message},
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            content_type="application/json",
        )
