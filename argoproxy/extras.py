import json
from datetime import datetime

from argoproxy.chat import (
    MODEL_AVAIL as CHAT_MODEL_AVAIL,
    proxy_request as chat_proxy_request,
)
from argoproxy.embed import MODEL_AVAIL as EMBED_MODEL_AVAIL
from flask import Response

# Combine the available models from chat.py and embed.py
ALL_MODELS = {**CHAT_MODEL_AVAIL, **EMBED_MODEL_AVAIL}

# Mock data for available models
MODELS_DATA = {"object": "list", "data": []}

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
    return Response(
        json.dumps(MODELS_DATA), status=200, content_type="application/json"
    )


def get_status():
    """
    Makes a real call to GPT-4o using the chat.py proxy_request function.
    """
    # Create a mock request to GPT-4o
    mock_request = {"model": "gpt-4o", "prompt": "Say hello", "user": "system"}

    # Use the chat_proxy_request function to make the call
    response = chat_proxy_request(convert_to_openai=True, input_data=mock_request)
    return response
