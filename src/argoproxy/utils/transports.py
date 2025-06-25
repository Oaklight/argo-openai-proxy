import json
from typing import Any, Dict, Union

from aiohttp import web


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
