import random
import socket

from loguru import logger


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
    if endpoint == "chat/completions":
        required_fields = ["model", "messages"]
    elif endpoint == "completions":
        required_fields = ["model", "prompt"]
    elif endpoint == "embeddings":
        required_fields = ["model", "input"]
    else:
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


def get_random_port(low: int, high: int) -> int:
    """
    Generates a random port within the specified range and ensures it is available.

    Args:
        low (int): The lower bound of the port range.
        high (int): The upper bound of the port range.

    Returns:
        int: A random available port within the range.

    Raises:
        ValueError: If no available port can be found within the range.
    """
    if low < 1024 or high > 65535 or low >= high:
        raise ValueError("Invalid port range. Ports should be between 1024 and 65535.")

    attempts = high - low  # Maximum attempts to check ports in the range
    for _ in range(attempts):
        port = random.randint(low, high)
        if is_port_available(port):
            return port

    raise ValueError(f"No available port found in the range {low}-{high}.")


def is_port_available(port: int, timeout: float = 0.1) -> bool:
    """
    Checks if a given port is available (not already in use).

    Args:
        port (int): The port number to check.
        timeout (float): Timeout in seconds for the connection attempt.

    Returns:
        bool: True if the port is available, False otherwise.
    """
    for family in (socket.AF_INET, socket.AF_INET6):
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.settimeout(timeout)
                s.bind(("127.0.0.1", port))
                s.close()
                return True
        except (OSError, socket.timeout):
            continue
    return False
