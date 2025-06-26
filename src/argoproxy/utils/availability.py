import argparse
import json
import urllib.request
from typing import Any, Dict, List

from loguru import logger
from pydantic import BaseModel

from ..config import validate_config
from ..models import _CHAT_MODELS
from .misc import make_bar


class Model(BaseModel):
    id: str
    model_name: str


def process_model_name(name: str) -> str:
    return name.lower().replace(" ", "-")


def get_upstream_model_list(url: str) -> List[Model]:
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
            for model in models:
                model.model_name = process_model_name(model.model_name)

            data = [each.model_dump() for each in models]
            return data
    except Exception as e:
        logger.error(f"Error fetching model list from {url}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Argo Proxy CLI",
    )

    # Validate config in main process only
    config_instance = validate_config(None, True)
    url = config_instance.argo_model_url
    model_list = get_upstream_model_list(url)
    logger.warning(json.dumps(model_list, indent=2))
