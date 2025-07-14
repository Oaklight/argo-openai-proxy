import asyncio
import json
import time
import uuid
from http import HTTPStatus
from typing import Any, Awaitable, Callable, Dict, List, Optional, Union, cast

import aiohttp
from aiohttp import web
from loguru import logger

from ..config import ArgoConfig
from ..models import ModelRegistry
from ..tool_calls.input_handle import handle_tools
from ..tool_calls.output_handle import (
    ToolInterceptor,
    tool_calls_to_openai,
    tool_calls_to_openai_stream,
)
from ..types import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChoiceDelta,
    CompletionUsage,
    NonStreamChoice,
    StreamChoice,
)
from ..types.chat_completion import FINISH_REASONS
from ..utils.input_handle import (
    handle_multiple_entries_prompt,
    handle_no_sys_msg,
    handle_option_2_input,
)
from ..utils.misc import make_bar
from ..utils.tokens import (
    calculate_prompt_tokens_async,
    count_tokens_async,
)
from ..utils.transports import pseudo_chunk_generator, send_off_sse

DEFAULT_MODEL = "argo:gpt-4o"


async def transform_chat_completions_streaming_async(
    content: Optional[str] = None,
    *,
    model_name: str,
    create_timestamp: int,
    finish_reason: FINISH_REASONS = "stop",
    tool_calls: Optional[Dict[str, Any]] = None,
    tc_index: int = 0,
    **kwargs,
) -> Dict[str, Any]:
    """
    Transforms the custom API response into a streaming OpenAI-compatible format.
    """

    # in stream mode we could only have one tool call at a time, but we need to wrap it in a list to match the tool_calls_to_openai_stream function signature
    try:
        # Handle tool calls for streaming
        tool_calls_obj = None
        if tool_calls:
            logger.warning(f"transforming tool_calls: {tool_calls}")
            # tool_calls_obj is None or List of ChoiceDeltaToolCall
            tool_calls_obj = [
                tool_calls_to_openai_stream(
                    tool_calls,
                    tc_index=tc_index,
                    api_format="chat_completion",
                )
            ]

        openai_response = ChatCompletionChunk(
            id=str(uuid.uuid4().hex),
            created=create_timestamp,
            model=model_name,
            choices=[
                StreamChoice(
                    index=0,
                    delta=ChoiceDelta(
                        content=content,
                        tool_calls=tool_calls_obj,
                    ),
                    finish_reason=finish_reason,
                )
            ],
        )
        return openai_response.model_dump()
    except Exception as err:
        return {"error": f"An error occurred in streaming response: {err}"}


async def transform_chat_completions_non_streaming_async(
    content: Optional[str] = None,
    *,
    model_name: str,
    create_timestamp: int,
    prompt_tokens: int,
    finish_reason: FINISH_REASONS = "stop",
    tool_calls: Optional[List[Dict[str, Any]]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Asynchronously transforms the custom API response into a non-streaming OpenAI-compatible format.
    """
    try:
        # Calculate token usage asynchronously
        completion_tokens = (
            await count_tokens_async(content, model_name) if content else 0
        )
        if tool_calls:
            tool_tokens = await count_tokens_async(json.dumps(tool_calls), model_name)
            completion_tokens += tool_tokens
        total_tokens = prompt_tokens + completion_tokens

        usage = CompletionUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        # Handle tool calls
        tool_calls_obj = None
        if tool_calls and isinstance(tool_calls, list):
            tool_calls_obj = tool_calls_to_openai(
                tool_calls, api_format="chat_completion"
            )

        openai_response = ChatCompletion(
            id=str(uuid.uuid4().hex),
            created=create_timestamp,
            model=model_name,
            choices=[
                NonStreamChoice(
                    index=0,
                    message=ChatCompletionMessage(
                        content=content,
                        tool_calls=tool_calls_obj,
                    ),
                    finish_reason=finish_reason,
                )
            ],
            usage=usage,
        )

        return openai_response.model_dump()

    except json.JSONDecodeError as err:
        return {"error": f"Error decoding JSON: {err}"}
    except Exception as err:
        return {"error": f"An error occurred in non-streaming response: {err}"}


def prepare_chat_request_data(
    data: Dict[str, Any],
    config: ArgoConfig,
    model_registry: ModelRegistry,
    *,
    enable_tools: bool = False,
) -> Dict[str, Any]:
    """
    Prepares chat request data for upstream APIs based on model type.

    Args:
        data: The incoming request data.
        config: The ArgoConfig object containing configuration settings.
        model_registry: The ModelRegistry object containing model mappings.
        enable_tools: Determines whether we enables tool calls related fields - tools, tool_choice, parallel_tool_calls.

    Returns:
        The modified request data.
    """
    # Automatically replace or insert user information
    data["user"] = config.user

    # Remap the model name
    if "model" not in data:
        data["model"] = DEFAULT_MODEL
    data["model"] = model_registry.resolve_model_name(data["model"], model_type="chat")

    # Convert prompt to list if necessary
    if "prompt" in data and not isinstance(data["prompt"], list):
        data["prompt"] = [data["prompt"]]

    if enable_tools:
        # convert tools related fields to a single system prompt
        data = handle_tools(data)
    else:
        # remove incompatible fields for direct ARGO API calls
        data.pop("tools", None)
        data.pop("tool_choice", None)
        data.pop("parallel_tool_calls", None)

    # Apply transformations based on model type
    if data["model"] in model_registry.option_2_input_models:
        # Transform data for models requiring `system` and `prompt` structure only
        data = handle_option_2_input(data)

    # flatten the list of strings into a single string in case of multiple prompts
    if isinstance(data.get("prompt"), list):
        data["prompt"] = ["\n\n".join(data["prompt"]).strip()]

    if data["model"] in model_registry.no_sys_msg_models:
        data = handle_no_sys_msg(data)

    data = handle_multiple_entries_prompt(data)

    # if config.verbose:
    #     logger.info(make_bar("Transformed Request"))
    #     logger.info(f"{json.dumps(data, indent=2)}")

    return data


async def send_non_streaming_request(
    session: aiohttp.ClientSession,
    api_url: str,
    data: Dict[str, Any],
    convert_to_openai: bool = False,
    openai_compat_fn: Union[
        Callable[..., Dict[str, Any]], Callable[..., Awaitable[Dict[str, Any]]]
    ] = transform_chat_completions_non_streaming_async,
) -> web.Response:
    """Sends a non-streaming request to an API and processes the response.

    Args:
        session: The client session for making the request.
        api_url: URL of the API endpoint.
        data: The JSON payload of the request.
        convert_to_openai: If True, converts the response to OpenAI format.
        openai_compat_fn: Function for conversion to OpenAI-compatible format.

    Returns:
        A web.Response with the processed JSON data.
    """
    headers = {"Content-Type": "application/json"}
    async with session.post(api_url, headers=headers, json=data) as upstream_resp:
        response_data = await upstream_resp.json()
        upstream_resp.raise_for_status()

        if convert_to_openai:
            # Calculate prompt tokens asynchronously
            prompt_tokens = await calculate_prompt_tokens_async(data, data["model"])
            content = response_data["response"]

            cs = ToolInterceptor()
            tool_calls, clean_text = cs.process(content)
            finish_reason = "tool_calls" if tool_calls else "stop"

            # Check if the function is async and call accordingly
            if asyncio.iscoroutinefunction(openai_compat_fn):
                openai_response = await openai_compat_fn(
                    clean_text,
                    model_name=data.get("model"),
                    create_timestamp=int(time.time()),
                    prompt_tokens=prompt_tokens,
                    finish_reason=finish_reason,
                    tool_calls=tool_calls,
                )
            else:
                openai_response = openai_compat_fn(
                    clean_text,
                    model_name=data.get("model"),
                    create_timestamp=int(time.time()),
                    prompt_tokens=prompt_tokens,
                    finish_reason=finish_reason,
                    tool_calls=tool_calls,
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
    request: web.Request,
    convert_to_openai: bool = False,
    *,
    openai_compat_fn: Union[
        Callable[..., Dict[str, Any]],
        Callable[..., Awaitable[Dict[str, Any]]],
    ] = transform_chat_completions_streaming_async,
    fake_stream: bool = False,
) -> web.StreamResponse:
    """Sends a streaming request to an API and streams the response to the client.

    Args:
        session: The client session for making the request.
        api_url: URL of the API endpoint.
        data: The JSON payload of the request.
        request: The web request used for streaming responses.
        convert_to_openai: If True, converts the response to OpenAI format.
        openai_compat_fn: Function for conversion to OpenAI-compatible format.
        fake_stream: If True, simulates streaming by sending the response in chunks.
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "text/plain",
        "Accept-Encoding": "identity",
    }

    # Set response headers based on the mode
    created_timestamp = int(time.time())
    prompt_tokens = await calculate_prompt_tokens_async(data, data["model"])
    if convert_to_openai:
        response_headers = {"Content-Type": "text/event-stream"}
    else:
        response_headers = {"Content-Type": "text/plain; charset=utf-8"}

    if fake_stream:
        data["stream"] = False  # disable streaming in upstream request

    async with session.post(api_url, headers=headers, json=data) as upstream_resp:
        if upstream_resp.status != 200:
            # Read error content from upstream response
            error_text = await upstream_resp.text()
            # Return JSON error response to client
            return web.json_response(
                {"error": f"Upstream API error: {upstream_resp.status} {error_text}"},
                status=upstream_resp.status,
                content_type="application/json",
            )

        # Initialize the streaming response
        response_headers.update(
            {
                k: v
                for k, v in upstream_resp.headers.items()
                if k.lower()
                not in (
                    "content-type",
                    "content-encoding",
                    "transfer-encoding",
                    "content-length",  # in case of fake streaming
                )
            }
        )
        response = web.StreamResponse(
            status=upstream_resp.status,
            headers=response_headers,
        )

        response.enable_chunked_encoding()
        await response.prepare(request)

        if fake_stream:
            # Get full response first
            response_data = await upstream_resp.json()
            response_text = response_data.get("response", "")

            if convert_to_openai:
                # OpenAI conversion & tool calls logic only applies below
                cs = ToolInterceptor()
                tool_calls, cleaned_text = cs.process(response_text)

                if tool_calls:
                    for i, tc_dict in enumerate(tool_calls):
                        # Ensure proper handling for both sync and async conversion functions
                        if asyncio.iscoroutinefunction(openai_compat_fn):
                            chunk_json = await openai_compat_fn(
                                None,
                                model_name=data["model"],
                                create_timestamp=created_timestamp,
                                prompt_tokens=prompt_tokens,
                                is_streaming=True,
                                finish_reason="tool_calls",
                                tool_calls=tc_dict,
                                tc_index=i,
                            )
                        else:
                            chunk_json = openai_compat_fn(
                                None,
                                model_name=data["model"],
                                create_timestamp=created_timestamp,
                                prompt_tokens=prompt_tokens,
                                is_streaming=True,
                                finish_reason="tool_calls",
                                tool_calls=tc_dict,
                                tc_index=i,
                            )
                        await send_off_sse(response, cast(Dict[str, Any], chunk_json))

                total_processed = 0
                async for chunk_text in pseudo_chunk_generator(cleaned_text):
                    total_processed += len(chunk_text)
                    finish_reason = None
                    if total_processed >= len(cleaned_text):
                        finish_reason = "stop"

                    if asyncio.iscoroutinefunction(openai_compat_fn):
                        chunk_json = await openai_compat_fn(
                            chunk_text,
                            model_name=data["model"],
                            create_timestamp=created_timestamp,
                            prompt_tokens=prompt_tokens,
                            is_streaming=True,
                            finish_reason=finish_reason,  # May be None for ongoing chunks
                            tool_calls=None,
                        )
                    else:
                        chunk_json = openai_compat_fn(
                            chunk_text,
                            model_name=data["model"],
                            create_timestamp=created_timestamp,
                            prompt_tokens=prompt_tokens,
                            is_streaming=True,
                            finish_reason=finish_reason,  # May be None for ongoing chunks
                            tool_calls=None,
                        )
                    await send_off_sse(response, cast(Dict[str, Any], chunk_json))

            else:
                # Simple: just raw chunk streaming
                async for chunk_text in pseudo_chunk_generator(response_text):
                    await send_off_sse(response, chunk_text.encode())
        else:
            # ATTENTION:
            # this branch is semi-stale, as upstream support to streaming mode is primitive. We shall deal with it when we need it.
            chunk_iterator = upstream_resp.content.iter_any()
            async for chunk_bytes in chunk_iterator:
                # Inline handle_chunk logic for real streaming mode
                logger.warning(f"Handling chunk: {chunk_bytes}")
                logger.warning(f"Finish reason: {None}")
                logger.warning(f"Tool calls before openai_compat_fn: {None}")
                if convert_to_openai:
                    # Convert the chunk to OpenAI-compatible JSON
                    if asyncio.iscoroutinefunction(openai_compat_fn):
                        chunk_json = await openai_compat_fn(
                            chunk_bytes.decode() if chunk_bytes else None,
                            model_name=data["model"],
                            create_timestamp=created_timestamp,
                            prompt_tokens=prompt_tokens,
                            is_streaming=True,
                            finish_reason=None,  # May be None for ongoing chunks
                            tool_calls=None,
                        )
                    else:
                        chunk_json = openai_compat_fn(
                            chunk_bytes.decode() if chunk_bytes else None,
                            model_name=data["model"],
                            create_timestamp=created_timestamp,
                            prompt_tokens=prompt_tokens,
                            is_streaming=True,
                            finish_reason=None,  # May be None for ongoing chunks
                            tool_calls=None,
                        )
                    await send_off_sse(response, cast(Dict[str, Any], chunk_json))
                else:
                    # Return the chunk as raw text
                    await send_off_sse(response, chunk_bytes)

        # Ensure response is properly closed
        await response.write_eof()

        return response


async def proxy_request(
    request: web.Request,
    *,
    convert_to_openai: bool = True,
) -> Union[web.Response, web.StreamResponse]:
    """Proxies the client's request to an upstream API, handling response streaming and conversion.

    Args:
        request: The client's web request object.
        convert_to_openai: If True, translates the response to an OpenAI-compatible format.

    Returns:
        A web.Response or web.StreamResponse with the final response from the upstream API.
    """
    config: ArgoConfig = request.app["config"]
    model_registry: ModelRegistry = request.app["model_registry"]

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
        data = prepare_chat_request_data(
            data, config, model_registry, enable_tools=convert_to_openai
        )

        # Use the shared HTTP session from app context for connection pooling
        session = request.app["http_session"]

        if stream:
            return await send_streaming_request(
                session,
                config.argo_url,
                data,
                request,
                convert_to_openai,
                fake_stream=True,
            )
        else:
            return await send_non_streaming_request(
                session,
                config.argo_url,
                data,
                convert_to_openai,
                openai_compat_fn=transform_chat_completions_non_streaming_async,
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
