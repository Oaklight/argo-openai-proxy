import fnmatch
import json
import time
import uuid
from http import HTTPStatus
from typing import Any, Callable, Dict

import aiohttp
from aiohttp import web
from loguru import logger

from ..config import ArgoConfig
from ..constants import CHAT_MODELS
from ..types import (
    Response,
    ResponseOutputMessage,
    ResponseOutputText,
    ResponseUsage,
)
from ..utils import (
    count_tokens,
    make_bar,
    resolve_model_name,
)
from .chat import send_non_streaming_request

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

INCOMPATIBLE_INPUT_FIELDS = {
    "include",
    "metadata",
    "parallel_tool_calls",
    "previous_response_id",
    "reasoning",
    "service_tier",
    "store",
    "text",
    "tool_choice",
    "tools",
    "truncation",
}


def make_it_openai_responses_compat(
    custom_response: Any,
    model_name: str,
    create_timestamp: int,
    prompt_tokens: int,
    is_streaming: bool = False,
    finish_reason: str = None,
) -> Dict[str, Any]:
    """
    Transforms the custom API response into a format compatible with OpenAI's API.

    Args:
        custom_response: The response obtained from the custom API.
        model_name: The name of the model that generated the completion.
        create_timestamp: The creation timestamp of the completion.
        prompt_tokens: The number of tokens in the input prompt.
        is_streaming: Boolean indicating if the response is streaming.
        finish_reason: The reason for response completion, e.g., "stop".

    Returns:
        A dictionary representing the OpenAI-compatible JSON response.
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
            usage = ResponseUsage(
                input_tokens=prompt_tokens,
                output_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

        if is_streaming:
            raise NotImplementedError("Streaming is not implemented yet.")
        else:
            id = str(uuid.uuid4().hex)
            openai_response = Response(
                id=f"resp_{id}",
                created_at=create_timestamp,
                model=model_name,
                output=[
                    ResponseOutputMessage(
                        id=f"msg_{id}",
                        status="completed",
                        content=[
                            ResponseOutputText(
                                text=response_text,
                            )
                        ],
                    )
                ],
                status="completed",
                usage=usage,
            )

        return openai_response.model_dump()

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred: {err}"}


def prepare_request_data(
    data: Dict[str, Any],
    request: web.Request,
) -> Dict[str, Any]:
    """
    Modifies and prepares the incoming request data by adding user information
    and remapping the model according to configurations.

    Args:
        data: The original request data.
        request: The incoming web request object.

    Returns:
        The modified and prepared request data.
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

    # obtain messages from input
    messages = data.get("input", [])
    # Insert instructions as a system message
    if instructions := data.get("instructions", ""):
        messages.insert(0, {"role": "system", "content": instructions})
        del data["instructions"]
    # replace input with messages
    data["messages"] = messages
    del data["input"]

    if max_tokens := data.get("max_output_tokens", None):
        data["max_tokens"] = max_tokens
        del data["max_output_tokens"]

    # Convert system message to user message for specific models
    if data["model"] in NO_SYS_MSG:
        if "messages" in data:
            for message in data["messages"]:
                if message["role"] == "system":
                    message["role"] = "user"

    # drop other unsupported fields
    for key in list(data.keys()):
        if key in INCOMPATIBLE_INPUT_FIELDS:
            del data[key]
    return data




async def send_streaming_request(
    session: aiohttp.ClientSession,
    api_url: str,
    data: Dict[str, Any],
    request: web.Request,
    convert_to_openai: bool = False,
    openai_compat_fn: Callable[..., Dict[str, Any]] = make_it_openai_responses_compat,
) -> None:
    raise NotImplementedError("Streaming requests are not yet supported.")


async def proxy_request(
    request: web.Request,
    *,
    convert_to_openai: bool = False,
) -> web.Response:
    """Proxies the client's request to an upstream API, handling response streaming and conversion.

    Args:
        request: The client's web request object.
        convert_to_openai: If True, translates the response to an OpenAI-compatible format.

    Returns:
        A web.Response with the final response from the upstream API.
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
                    openai_compat_fn=make_it_openai_responses_compat,
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
