import json
import os
import sys
import urllib
from dataclasses import asdict, dataclass
from typing import Optional

import yaml
from loguru import logger

from argoproxy.utils import get_random_port, is_port_available

logger.remove()  # Remove default handlers
logger.add(sys.stdout, colorize=True, format="<level>{message}</level>", level="INFO")

PATHS_TO_TRY = [
    os.path.expanduser("~/.config/argoproxy/config.yaml"),
    os.path.expanduser("~/.argoproxy/config.yaml"),
    "./config.yaml",
]


def validate_api(url: str, username: str, payload: dict) -> bool:
    """
    Helper to validate API endpoint connectivity.
    Args:
        url (str): The API URL to validate.
        username (str): The username included in the request payload.
        payload (dict): The request payload in dictionary format.

    Returns:
        bool: True if validation succeeds, False otherwise.
    Raises:
        ValueError: If validation fails
    """
    payload["user"] = username
    request_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=request_data, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=1) as response:
            if response.getcode() != 200:
                raise ValueError(f"API returned status code {response.getcode()}")
            return True
    except Exception as e:
        raise ValueError(f"API validation failed for {url}: {str(e)}") from e


@dataclass
class ArgoConfig:
    """Configuration values with validation and interactive methods."""

    REQUIRED_KEYS = [
        "port",
        "argo_url",
        "argo_embedding_url",
        "user",
        "num_workers",
        "timeout",
    ]

    # Configuration fields with default values
    port: int = 44497
    argo_url: str = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
    argo_stream_url: str = (
        "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
    )
    argo_embedding_url: str = (
        "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
    )
    user: str = ""
    verbose: bool = True
    num_workers: int = 5
    timeout: int = 600
    logging_level: str = "INFO"

    @classmethod
    def from_dict(cls, config_dict: dict):
        """Create ArgoConfig instance from a dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})

    def to_dict(self) -> dict:
        """Convert ArgoConfig instance to a dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """Provide a formatted string representation for logger.infoing."""
        return json.dumps(self.to_dict(), indent=4)

    def validate(self, creation_mode: bool = False) -> None:
        """
        Validate and patch all configuration aspects.

        Args:
           creation_mode (bool): If True, it's assumed that this is the first time the config is being created.
        """
        # First ensure all required keys exist (but don't validate values yet)
        config_dict = self.to_dict()
        for key in self.REQUIRED_KEYS:
            if key not in config_dict:
                raise ValueError(f"Missing required configuration: '{key}'")

        # Then validate and patch individual components
        self._validate_user()  # Handles empty user
        logger.info("")
        self._validate_port()  # Handles invalid port
        logger.info("")
        self._validate_urls()  # Handles URL validation with skip option
        logger.info("")
        self._get_verbose(first_time=creation_mode)  # Handles verbose flag
        logger.info("")

    def _validate_user(self) -> None:
        """
        Validate and update the user attribute interactively.
        Ensures user is not empty, contains no whitespace, and is not 'cels'.
        If user is empty, prompts for input until valid.
        """
        while True:
            if not self.user:
                self.user = input(
                    "Username cannot be empty. Enter your username: "
                ).strip()
                continue
            if " " in self.user:
                logger.warning("Invalid username: Must not contain spaces.")
                self.user = input("Enter a valid username: ").strip()
                continue
            if self.user.lower() == "cels":
                logger.warning("Invalid username: 'cels' is not allowed.")
                self.user = input("Enter a valid username: ").strip()
                continue
            break

    def _validate_port(self) -> None:
        """Validate and patch the port attribute."""
        if self.port and is_port_available(self.port):
            logger.info(f"Using port {self.port}...")
            return  # Valid port already set

        if self.port:
            logger.warning(f"Warning: Port {self.port} is already in use.")

        suggested_port = get_random_port(49152, 65535)
        logger.info(f"Suggested available port: {suggested_port}")

        if input(f"Use port {suggested_port}? [y/N]: ").lower() == "y":
            self.port = suggested_port
            logger.info(f"Using port {self.port}...")
        else:
            raise ValueError("Port selection aborted by user")

    def _validate_urls(self) -> None:
        """Validate URL connectivity with option to skip failures."""
        required_urls = [
            (
                self.argo_url,
                {
                    "model": "gpt4o",
                    "messages": [{"role": "user", "content": "What are you?"}],
                },
            ),
            (self.argo_embedding_url, {"model": "v3small", "prompt": ["hello"]}),
        ]

        logger.info("Validating URL connectivity...")
        errors = []

        for url, payload in required_urls:
            if not url.startswith(("http://", "https://")):
                errors.append(f"Invalid URL format: {url}")
                continue

            try:
                validate_api(url, self.user, payload)
            except Exception as e:
                errors.append(f"{url}: {str(e)}")

        if errors:
            logger.error("URL validation errors:")
            for error in errors:
                logger.error(f"- {error}")

            choice = (
                input("Continue despite connectivity issue? [Y/n] ").strip().lower()
            )
            if choice not in ("", "y", "yes"):
                raise ValueError("URL validation aborted by user")
            logger.info("Continuing with configuration despite URL issues...")

    def _get_verbose(self, first_time: bool = False) -> None:
        """
        Toggle verbose mode based on existing settings or user input.
        Checks for self.verbose preset or VERBOSE environment variable first.
        Only prompts user if first_time is True or no setting was found.
        """

        # Check environment variable
        env_verbose = os.getenv("VERBOSE", "").lower()
        if env_verbose in ("1", "true", "yes"):
            self.verbose = True
            logger.info("Verbose mode enabled (from environment VERBOSE)")
        elif env_verbose in ("0", "false", "no"):
            self.verbose = False
            logger.info("Verbose mode disabled (from environment VERBOSE)")

        # Check for existing verbosity setting
        if self.verbose is not None and not first_time:
            return

        # Only prompt if first_time or no setting was found
        while True:
            verbose = input("Enable verbose mode? [Y/n] ").strip().lower()
            if verbose in ("", "y", "yes"):
                self.verbose = True
                break
            elif verbose in ("n", "no"):
                self.verbose = False
                break
            else:
                logger.info("Invalid input.")

    def show(self, message: Optional[str] = None) -> None:
        """
        Display the current configuration in a formatted manner.

        Args:
            message (Optional[str]): Message to display before showing the configuration.
        """
        logger.info(message if message else "Current configuration:")
        logger.info("--------------------------------------")
        logger.info(self)  # Use the __str__ method for formatted output
        logger.info("--------------------------------------")


def create_config() -> ArgoConfig:
    """Interactive method to create and persist config."""
    # Get home directory, with fallback to expanduser if HOME is not set
    home_dir = os.getenv("HOME") or os.path.expanduser("~")
    config_path = os.path.join(home_dir, ".config", "argoproxy", "config.yaml")

    logger.info(f"Creating new configuration at: {config_path}")
    config_data = ArgoConfig()  # Create a default ArgoConfig instance
    config_data.show()
    config_data.validate(creation_mode=True)

    # Save to config file
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config_data.to_dict(), f)

    return config_data


def load_config(optional_path: Optional[str] = None) -> ArgoConfig:
    """Load configuration from an optional path or predefined paths, or create one interactively.

    Args:
        optional_path (Optional[str]): Specific path to load the configuration from. Defaults to None.

    Returns:
        ArgoConfig: Loaded or newly created configuration instance.
    """
    config_data = None

    # Check if the optional path is provided and valid
    if optional_path and os.path.exists(optional_path):
        logger.info(f"Loading config from specified path: {optional_path}")
        with open(optional_path, "r") as f:
            try:
                config_dict = yaml.safe_load(f)
                config_data = ArgoConfig.from_dict(config_dict)
                config_data.validate()
            except (yaml.YAMLError, AssertionError) as e:
                logger.info(f"Error loading configuration file at {optional_path}: {e}")
                config_data = None  # Reset config_data to None on error
    else:
        # Iterate over predefined paths if optional_path is not provided or invalid
        for path in PATHS_TO_TRY:
            if os.path.exists(path):
                logger.info(f"Loading config from: {path}")
                with open(path, "r") as f:
                    try:
                        config_dict = yaml.safe_load(f)
                        config_data = ArgoConfig.from_dict(config_dict)
                        config_data.validate()
                    except (yaml.YAMLError, AssertionError) as e:
                        logger.info(f"Error loading configuration file at {path}: {e}")
                        config_data = None  # Reset config_data to None on error
                break

    # If no valid config is found, create a new one interactively
    if config_data is None:
        logger.info(
            "No valid configuration found. Creating a new configuration interactively..."
        )
        config_data = create_config()

    config_data.show("Configuration loaded successfully:")
    return config_data


# Use the environment variable `CONFIG_PATH` or fallback to predefined locations
config_path = os.getenv("CONFIG_PATH", None)

try:
    config_instance = load_config(config_path)

    # Set global configuration variable as a dictionary
    config = config_instance.to_dict()
    logger.info("Configuration validated and set successfully.")
except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
    logger.error(f"Error loading or validating configuration: {e}")
    sys.exit(1)
