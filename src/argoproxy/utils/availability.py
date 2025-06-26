import argparse
import fnmatch
import json
import time
import urllib.request
from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel

from ..utils.transports import validate_api

from ..config import validate_config
from ..models import CHAT_MODELS
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


def streamable_list(stream_url: str, non_stream_url: str, user: str) -> bool:
    """
    Checks if the model is streamable.
    Args:
        model_name (str): The name of the model.
    Returns:
        bool: True if the model is streamable, False otherwise.
    """
    payload = {
        "model": None,
        "messages": [{"role": "user", "content": "What are you?"}],
    }
    for model_name, model_id in CHAT_MODELS.items():
        payload["model"] = model_id
        try:
            validate_api(stream_url, user, payload, timeout=15)
            logger.info(f"Streamable model: {model_name}")
        except Exception as e:
            logger.error(f"Error validating streamable model {model_name}: {e}")


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

    streamable_list(
        config_instance.argo_stream_url,
        config_instance.argo_url,
        config_instance.user,
    )
