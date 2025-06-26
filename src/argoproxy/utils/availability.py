import argparse
import json
import urllib.request
from typing import Any, Dict

from loguru import logger

from ..config import validate_config
from ..models import _CHAT_MODELS
from .misc import make_bar


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
            data = response.read().decode()
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
