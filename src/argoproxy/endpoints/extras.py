from typing import Optional

import aiohttp
from aiohttp import web

from ..models import ModelRegistry


def get_models(request: web.Request):
    """
    Returns a list of available models in OpenAI-compatible format.
    """
    model_registry: ModelRegistry = request.app["model_registry"]
    return web.json_response(model_registry.as_openai_list(), status=200)


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
