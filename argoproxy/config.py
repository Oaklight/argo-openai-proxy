import json
import os
import sys
import urllib
from typing import Optional

import yaml
from sanic.log import logger

from argoproxy.utils import get_random_port, is_port_available

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

    def __init__(self, skip_validation: bool = False):
        self.port = 44497
        self.argo_url = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
        self.argo_stream_url = (
            "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
        )
        self.argo_embedding_url = (
            "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
        )
        self.user = ""
        self.verbose = True
        self.num_workers = 5
        self.timeout = 600

        if not skip_validation:
            self.validate_user()
            self.validate_port()
            self.validate_urls()

    @classmethod
    def from_dict(cls, config_dict: dict):
        """Create ArgoConfig instance from a dictionary."""
        instance = cls()  # Skip initial validation
        for key, value in config_dict.items():
            if hasattr(instance, key):
                setattr(instance, key, value)

        # Only validate required keys presence, not values
        instance.validate_required_keys()
        return instance

    def to_dict(self) -> dict:
        """Convert ArgoConfig instance to a dictionary."""
        return {
            "port": self.port,
            "argo_url": self.argo_url,
            "argo_stream_url": self.argo_stream_url,
            "argo_embedding_url": self.argo_embedding_url,
            "user": self.user,
            "verbose": self.verbose,
            "num_workers": self.num_workers,
            "timeout": self.timeout,
        }

    def __str__(self) -> str:
        """Provide a formatted string representation for printing."""
        return json.dumps(self.to_dict(), indent=4)

    def validate_required_keys(self, config_path: str = "unknown_path") -> None:
        """
        Validate that all required keys are present in the configuration instance.
        This version doesn't trigger full validations, just checks for presence.
        """
        config_dict = self.to_dict()
        for key in self.REQUIRED_KEYS:
            if key not in config_dict:
                raise ValueError(f"{config_path} is missing the '{key}' variable.")

    def validate_user(self) -> None:
        """
        Validate and update the user attribute interactively.
        Ensures user is not empty, contains no whitespace, and is not 'cels'.
        """
        while not self.user or self.user.lower() == "cels" or " " in self.user:
            if not self.user or " " in self.user:
                print("Invalid username: Must not be empty or contain spaces.")
            elif self.user.lower() == "cels":
                print("Invalid username: 'cels' is not allowed.")
            self.user = input("Enter a valid username: ").strip()

    def validate_port(self) -> None:
        """Validate the port attribute."""
        if not is_port_available(self.port):
            print(f"Warning: Port {self.port} is already in use.")
            suggested_port = get_random_port(49152, 65535)
            print(f"Suggested available port: {suggested_port}")
            self.port = suggested_port
            print(f"Using port {self.port}...")

    def validate_urls(self) -> None:
        """
        Validate connectivity to all URLs with streamlined logic and logging.
        Prompts user only once if any validation fails.
        """
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

        print("Validating URL connectivity...")
        failed_urls = []

        # First try all validations without user interaction
        for url, payload in required_urls:
            try:
                if not url.startswith(("http://", "https://")):
                    raise ValueError(f"Invalid URL format: {url}")
                validate_api(url, self.user, payload)  # Will raise on failure
            except Exception as e:
                failed_urls.append((url, str(e)))

        # If any failed, prompt user once
        if failed_urls:
            print("\nValidation failed for:")
            for url, error in failed_urls:
                print(f"- {url}: {error}")

            while True:
                user_input = (
                    input("\nDo you want to continue anyway? [Y/n] ").strip().lower()
                )
                if user_input in ("y", "yes", ""):
                    print("Continuing with invalid URLs...")
                    break
                elif user_input in ("n", "no"):
                    raise ValueError("URL validation aborted by user")
                else:
                    print("Invalid input. Please enter 'Y' or 'N'")

        print("URL validation complete.")

    def get_verbose(self) -> None:
        """
        Toggle verbose mode based on user input.
        Updates the verbose attribute.
        """
        while True:
            verbose = input("Enable verbose mode? [Y/n] ").strip().lower()
            if verbose in ("", "y", "yes"):
                self.verbose = True
                break
            elif verbose in ("n", "no"):
                self.verbose = False
                break
            else:
                print("Invalid input.")

    def show(self, message: Optional[str] = None) -> None:
        """
        Display the current configuration in a formatted manner.

        Args:
            message (Optional[str]): Message to display before showing the configuration.
        """
        print(message if message else "Current configuration:")
        print("--------------------------------------")
        print(self)  # Use the __str__ method for formatted output
        print("--------------------------------------")


def create_config() -> ArgoConfig:
    """Interactive method to create and persist config."""
    # Get home directory, with fallback to expanduser if HOME is not set
    home_dir = os.getenv("HOME") or os.path.expanduser("~")
    config_path = os.path.join(home_dir, ".config", "argoproxy", "config.yaml")

    config_data = ArgoConfig()  # Create a default ArgoConfig instance

    # Save to config file
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config_data.to_dict(), f)

    config_data.show(f"Configuration saved to: {config_path}")
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
        print(f"Loading config from specified path: {optional_path}")
        with open(optional_path, "r") as f:
            try:
                config_dict = yaml.safe_load(f)
                config_data = ArgoConfig.from_dict(config_dict)
                config_data.validate_required_keys(optional_path)
            except (yaml.YAMLError, AssertionError) as e:
                print(f"Error loading configuration file at {optional_path}: {e}")
                config_data = None  # Reset config_data to None on error
    else:
        # Iterate over predefined paths if optional_path is not provided or invalid
        for path in PATHS_TO_TRY:
            if os.path.exists(path):
                print(f"Loading config from: {path}")
                with open(path, "r") as f:
                    try:
                        config_dict = yaml.safe_load(f)
                        config_data = ArgoConfig.from_dict(config_dict)
                        config_data.validate_required_keys(path)
                    except (yaml.YAMLError, AssertionError) as e:
                        print(f"Error loading configuration file at {path}: {e}")
                        config_data = None  # Reset config_data to None on error
                break

    # If no valid config is found, create a new one interactively
    if config_data is None:
        print(
            "No valid configuration found. Creating a new configuration interactively..."
        )
        config_data = create_config()

    config_data.show("Configuration loaded successfully:")
    return config_data


# Use the environment variable `CONFIG_PATH` or fallback to predefined locations
config_path = os.getenv("CONFIG_PATH", None)

try:
    config_instance = load_config()

    # Set global configuration variable as a dictionary
    config = config_instance.to_dict()
    logger.info("Configuration validated and set successfully.")
except (FileNotFoundError, yaml.YAMLError, ValueError) as e:
    logger.error(f"Error loading or validating configuration: {e}")
    sys.exit(1)
