import asyncio
import json
import urllib.request
from typing import Any, AsyncGenerator, Dict, Union

from aiohttp import web


async def pseudo_chunk_generator(
    complete_text: str,
    chunk_size: int = 30,
    sleep_time: float = 0.01,
) -> AsyncGenerator[str, None]:
    """Generate text chunks asynchronously to simulate streaming responses.

    Args:
        complete_text: The complete text to be chunked.
        chunk_size: Size of each chunk in characters. Defaults to 20.
        sleep_time: Time to sleep between chunks in seconds. Defaults to 0.02.

    Yields:
        str: Text chunks of the specified size.

    Example:
        >>> async for chunk in pseudo_chunk_generator("Hello World", 5):
        ...     print(chunk)
        "Hello"
        " Worl"
        "d"
    """
    for i in range(0, len(complete_text), chunk_size):
        chunk = complete_text[i : i + chunk_size]
        await asyncio.sleep(sleep_time)  # Small delay between chunks
        yield chunk


async def send_off_sse(
    response: web.StreamResponse, data: Union[Dict[str, Any], bytes]
) -> None:
    """
    Sends a chunk of data as a Server-Sent Events (SSE) event.

    Args:
        response (web.StreamResponse): The response object used to send the SSE event.
        data (Union[Dict[str, Any], bytes]): The chunk of data to be sent as an SSE event.
            It can be either a dictionary (which will be converted to a JSON string and then to bytes)
            or preformatted bytes.

    Returns:
        None
    """
    # Send the chunk as an SSE event
    if isinstance(data, bytes):
        sse_chunk = data
    else:
        # Convert the chunk to OpenAI-compatible JSON and then to bytes
        sse_chunk = f"data: {json.dumps(data)}\n\n".encode()
    await response.write(sse_chunk)


def validate_api(url: str, username: str, payload: dict, timeout: int = 2) -> bool:
    """
    Helper to validate API endpoint connectivity.
    Args:
        url (str): The API URL to validate.
        username (str): The username included in the request payload.
        payload (dict): The request payload in dictionary format.

    Returns:
        bool: True if validation succeeds, False otherwise.
    Raises:
        ValueError: If validation fails
    """
    payload["user"] = username
    request_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=request_data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.getcode() != 200:
                raise ValueError(f"API returned status code {response.getcode()}")
            return True
    except Exception as e:
        raise ValueError(f"API validation failed for {url}: {str(e)}") from e


async def validate_api_async(url, user, payload, timeout, attempts=3):
    """
    Asynchronously validates API connectivity with attempts.

    Args:
        url (str): The API URL to validate.
        user (str): The username for payload.
        payload (dict): Request payload.
        timeout (int): Request timeout seconds.
        attempts (int): Total attempts (including the first).

    Returns:
        bool: True if validation succeeds.

    Raises:
        ValueError if all attempts fail.
    """
    last_err = None
    for attempt in range(attempts + 1):  # tries = 1 + attempts
        try:
            return await asyncio.to_thread(
                validate_api, url, user, payload, timeout=timeout
            )
        except Exception as e:
            last_err = e
            if attempt < attempts:
                await asyncio.sleep(0.5)

    # If we reach here, all attempts failed
    if last_err is not None:
        raise last_err
    raise ValueError("API validation failed after all attempts")
