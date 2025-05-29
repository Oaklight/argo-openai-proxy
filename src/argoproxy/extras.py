import json
from datetime import datetime
from typing import Any, Dict

from sanic import response

from .chat import proxy_request as chat_proxy_request
from .constants import ALL_MODELS

# Mock data for available models
MODELS_DATA: Dict[str, Any] = {"object": "list", "data": []}  # type: ignore

# Populate the models data with the combined models
for model_id, model_name in ALL_MODELS.items():
    MODELS_DATA["data"].append(
        {
            "id": model_id,  # Include the key (e.g., "argo:gpt-4o")
            "object": "model",
            "created": int(
                datetime.now().timestamp()
            ),  # Use current timestamp for simplicity
            "owned_by": "system",  # Default ownership
            "internal_name": model_name,  # Include the value (e.g., "gpt4o")
        }
    )


def get_models():
    """
    Returns a list of available models in OpenAI-compatible format.
    """
    return response.json(MODELS_DATA, status=200)


async def get_status():
    """
    Makes a real call to GPT-4o using the chat.py proxy_request function.
    """
    # Create a mock request to GPT-4o
    mock_request = {"model": "gpt-4o", "prompt": "Say hello", "user": "system"}

    # Use the chat_proxy_request function to make the call
    response_data = await chat_proxy_request(
        convert_to_openai=True, input_data=mock_request
    )

    # Extract the JSON data from the JSONResponse object
    json_data = response_data.body

    # Return the JSON data as a new JSONResponse
    return response.json(json.loads(json_data), status=200)
