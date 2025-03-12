import re
from typing import Optional

from sanic.log import logger


def make_bar(message: str = "", bar_length=40) -> str:
    message = " " + message.strip() + " "
    message = message.strip()
    dash_length = (bar_length - len(message)) // 2
    message = "-" * dash_length + message + "-" * dash_length
    return message


def validate_input(json_input: dict, endpoint: str) -> bool:
    """
    Validates the input JSON to ensure it contains the necessary fields.
    """
    match endpoint:
        case "chat/completions":
            required_fields = ["model", "messages"]
        case "completions":
            required_fields = ["model", "prompt"]
        case "embeddings":
            required_fields = ["model", "input"]
        case _:
            logger.error(f"Unknown endpoint: {endpoint}")
            return False

    # check required field presence and type
    for field in required_fields:
        if field not in json_input:
            logger.error(f"Missing required field: {field}")
            return False
        if field == "messages" and not isinstance(json_input[field], list):
            logger.error(f"Field {field} must be a list")
            return False
        if field == "prompt" and not isinstance(json_input[field], (str, list)):
            logger.error(f"Field {field} must be a string or list")
            return False
        if field == "input" and not isinstance(json_input[field], (str, list)):
            logger.error(f"Field {field} must be a string or list")
            return False

    return True
