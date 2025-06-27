import argparse
import asyncio
import fnmatch
import json
import urllib.request
from typing import Any, Dict, List, Tuple

from httpx import stream
from loguru import logger
from pydantic import BaseModel

from ..config import validate_config
from ..models import CHAT_MODELS
from ..utils.transports import validate_api
from .misc import make_bar


class Model(BaseModel):
    id: str
    model_name: str


GPT_O_PATTERN = "gpto*"
CLAUDE_PATTERN = "claude*"


def produce_argo_model_list(upstream_models: List[Model]) -> Dict[str, Any]:
    """
    Generates a dictionary mapping standardized Argo model identifiers to their corresponding IDs.

    Args:
        upstream_models (List[Model]): A list of Model objects containing `model_name` and `id`.

    Returns:
        Dict[str, Any]: A dictionary where keys are formatted Argo model identifiers
                        (e.g., "argo:gpt-4o", "argo:claude-4-opus") and values are model IDs.

    The method creates special cases for specific models like GPT-O and Claude, adding additional granularity
    in the naming convention. It appends regular model mappings under the `argo:` prefix for all models.
    """
    argo_models = {}
    for model in upstream_models:
        model.model_name = model.model_name.replace(" ", "-").lower()

        if fnmatch.fnmatch(model.id, GPT_O_PATTERN):
            # special: argo:gpt-o1
            argo_models[f"argo:gpt-{model.model_name}"] = model.id

        elif fnmatch.fnmatch(model.id, CLAUDE_PATTERN):
            _, codename, gen_num, *version = model.model_name.split("-")
            if version:
                # special: argo:claude-3.5-sonnet-v2
                argo_models[f"argo:claude-{gen_num}-{codename}-{version[0]}"] = model.id
            else:
                # special: argo:claude-4-opus
                argo_models[f"argo:claude-{gen_num}-{codename}"] = model.id

        # regular: argo:gpt-4o, argo:o1 or argo:claude-opus-4
        argo_models[f"argo:{model.model_name}"] = model.id

    return argo_models


def get_upstream_model_list(url: str) -> Dict[str, Any]:
    """
    Fetches the list of available models from the upstream server.
    Args:
        url (str): The URL of the upstream server.
    Returns:
       Dict[str, Any]: A dictionary containing the list of available models.
    """
    try:
        with urllib.request.urlopen(url) as response:
            raw_data = json.loads(response.read().decode())["data"]
            models = [Model(**model) for model in raw_data]

            argo_models = produce_argo_model_list(models)

            return argo_models
    except Exception as e:
        logger.error(f"Error fetching model list from {url}: {e}")
        return CHAT_MODELS


async def validate_api_async(stream_url, user, payload, timeout):
    # Wrap your validate_api call for async behavior, assuming validate_api runs synchronously
    return await asyncio.to_thread(
        validate_api, stream_url, user, payload, timeout=timeout
    )


async def streamable_list_async(
    stream_url: str, non_stream_url: str, user: str
) -> Tuple[List[str], List[str]]:
    """
    Asynchronously checks which models are streamable.
    Args:
        stream_url (str): The streaming URL.
        non_stream_url (str): The non-streaming URL used as a fallback.
        user (str): The user identifier.
    Returns:
        tuple: (list of streamable model names, list of unavailable model names)
    """
    payload = {
        "model": None,
        "messages": [{"role": "user", "content": "What are you?"}],
    }

    async def check_model(model_name, model_id, max_retries=2):
        payload_copy = payload.copy()
        payload_copy["model"] = model_id

        for attempt in range(max_retries):
            # Try streaming
            try:
                await validate_api_async(stream_url, user, payload_copy, timeout=15)
                return (model_name, True)
            except Exception as e_stream:
                logger.warning(
                    f"Streaming check failed for {model_name} (attempt {attempt + 1}): {e_stream}"
                )
                # Try non-stream as fallback
                try:
                    await validate_api_async(
                        non_stream_url, user, payload_copy, timeout=15
                    )
                    return (model_name, False)
                except Exception as e_non_stream:
                    logger.warning(
                        f"Non-stream check failed for {model_name} (attempt {attempt + 1}): {e_non_stream}"
                    )
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2**attempt)  # Exponential backoff
                        continue
                    logger.error(f"All attempts failed for {model_name}")
                    return (model_name, None)

    tasks = [
        check_model(model_name, model_id)
        for model_name, model_id in CHAT_MODELS.items()
    ]
    results = await asyncio.gather(*tasks)

    streamable = []
    non_streamable = []
    unavailable = []
    for model_name, status in results:
        if status is True:
            streamable.append(model_name)
            non_streamable.append(model_name)
        elif status is False:
            non_streamable.append(model_name)
        elif status is None:
            unavailable.append(model_name)

    return streamable, non_streamable, unavailable


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Argo Proxy CLI",
    )

    # Validate config in main process only
    config_instance = validate_config(None, True)
    url = config_instance.argo_model_url
    model_list = get_upstream_model_list(url)
    logger.warning(json.dumps(model_list, indent=2))

    logger.warning(json.dumps(CHAT_MODELS, indent=2))

    # check if CHAT_MODELS == model_list with hash
    if hash(json.dumps(CHAT_MODELS, sort_keys=True)) == hash(
        json.dumps(model_list, sort_keys=True)
    ):
        logger.info("CHAT_MODELS and model_list are the same")
    else:
        logger.warning("CHAT_MODELS and model_list are different")

    async def check_models():
        return await streamable_list_async(
            config_instance.argo_stream_url,
            config_instance.argo_url,
            config_instance.user,
        )

    streamable, non_streamable, unavailable = asyncio.run(check_models())
    logger.info(f"Streamable models: {streamable}")
    logger.info(f"Non-streamable models: {non_streamable}")
    logger.info(f"Unavailable models: {unavailable}")
