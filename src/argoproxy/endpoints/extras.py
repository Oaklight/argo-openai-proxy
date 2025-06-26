from datetime import datetime
from typing import Any, Dict, Optional

import aiohttp
from aiohttp import web

from ..models import ALL_MODELS

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
    return web.json_response(MODELS_DATA, status=200)


async def get_latest_pypi_version() -> Optional[str]:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://pypi.org/pypi/argo-proxy/json",
                headers={
                    "Cache-Control": "no-cache",
                    "Pragma": "no-cache",
                },  # Add these headers
                timeout=5,
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data["info"]["version"]
    except Exception:
        return None
