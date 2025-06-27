import asyncio
import json
import os
import threading
from dataclasses import asdict, dataclass
from hashlib import md5
from pathlib import Path
from typing import Any, Optional, Tuple, Union

import yaml  # type: ignore
from loguru import logger
from tqdm.asyncio import tqdm_asyncio

from .utils.misc import get_random_port, is_port_available, make_bar
from .utils.transports import validate_api_async

PATHS_TO_TRY = [
    "./config.yaml",
    os.path.expanduser("~/.config/argoproxy/config.yaml"),
    os.path.expanduser("~/.argoproxy/config.yaml"),
]


@dataclass
class ArgoConfig:
    """Configuration values with validation and interactive methods."""

    REQUIRED_KEYS = [
        "port",
        "argo_url",
        "argo_embedding_url",
        "user",
    ]

    # Configuration fields with default values
    host: str = "0.0.0.0"  # Default to 0.0.0.0
    port: int = 44497
    user: str = ""
    argo_url: str = "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
    argo_stream_url: str = (
        "https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/streamchat/"
    )
    argo_embedding_url: str = (
        "https://apps.inside.anl.gov/argoapi/api/v1/resource/embed/"
    )
    argo_model_url: str = "https://apps-dev.inside.anl.gov/argoapi/api/v1/models/"
    verbose: bool = True

    @classmethod
    def from_dict(cls, config_dict: dict):
        """Create ArgoConfig instance from a dictionary."""
        return cls(**{k: v for k, v in config_dict.items() if k in cls.__annotations__})

    def to_dict(self) -> dict:
        """Convert ArgoConfig instance to a dictionary."""
        return asdict(self)

    def validate(self) -> bool:
        """Validate and patch all configuration aspects.

        Returns:
            bool: True if configuration changed after validation. False otherwise.
        """
        # First ensure all required keys exist (but don't validate values yet)
        config_dict = self.to_dict()
        for key in self.REQUIRED_KEYS:
            if key not in config_dict:
                raise ValueError(f"Missing required configuration: '{key}'")

        hash_original = md5(json.dumps(config_dict).encode()).hexdigest()
        # Then validate and patch individual components
        self._validate_user()  # Handles empty user
        self._validate_port()  # Handles invalid port
        self._validate_urls()  # Handles URL validation with skip option
        self._get_verbose()  # Handles verbose flag
        hash_after_validation = md5(json.dumps(self.to_dict()).encode()).hexdigest()

        return hash_original != hash_after_validation

    def _validate_user(self) -> None:
        """Validate and update the user attribute using the helper function."""
        self.user = _get_valid_username(self.user)

    def _validate_port(self) -> None:
        """Validate and patch the port attribute."""
        if self.port and is_port_available(self.port):
            logger.info(f"Using port {self.port}...")
            return  # Valid port already set

        if self.port:
            logger.warning(f"Warning: Port {self.port} is already in use.")

        suggested_port = get_random_port(49152, 65535)
        self.port = _get_user_port_choice(
            prompt=f"Enter port [{suggested_port}] [Y/n/number]: ",
            default_port=suggested_port,
        )
        logger.info(f"Using port {self.port}...")

    def _validate_urls(self) -> None:
        """Validate URL connectivity using validate_api_async with default retries."""
        required_urls: list[tuple[str, dict[str, Any]]] = [
            (
                self.argo_url,
                {
                    "model": "gpt4o",
                    "messages": [{"role": "user", "content": "What are you?"}],
                },
            ),
            (self.argo_embedding_url, {"model": "v3small", "prompt": ["hello"]}),
        ]

        timeout = 2
        attempts = 2
        logger.info(
            f"Validating {len(required_urls)} URL connectivity with timeout {timeout}s and {attempts} attempts ..."
        )

        failed_urls = []

        async def _validate_single_url(url: str, payload: dict) -> None:
            if not url.startswith(("http://", "https://")):
                logger.error(f"Invalid URL format: {url}")
                failed_urls.append(url)
                return
            try:
                await validate_api_async(
                    url, self.user, payload, timeout=timeout, attempts=attempts
                )
            except Exception as e:
                failed_urls.append(url)

        async def _main():
            tasks = [
                _validate_single_url(url, payload) for url, payload in required_urls
            ]
            for fut in tqdm_asyncio.as_completed(
                tasks, total=len(tasks), desc="Validating URLs"
            ):
                await fut

        try:
            asyncio.run(_main())
        except RuntimeError:
            logger.error("Async validation failed unexpectedly.")
            raise

        if failed_urls:
            logger.error("Failed to validate the following URLs: ")
            for url in failed_urls:
                logger.error(url)

            if not _get_yes_no_input(
                prompt="Continue despite connectivity issue? [Y/n] ", default_choice="y"
            ):
                raise ValueError("URL validation aborted by user")
            logger.info("Continuing with configuration despite URL issues...")
        else:
            logger.info("All URLs connectivity validated successfully.")

    def _get_verbose(self) -> None:
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
        if self.verbose is not None:
            return

        # Only prompt if first_time or no setting was found
        self.verbose = _get_yes_no_input(prompt="Enable verbose mode? [Y/n] ")

    def __str__(self) -> str:
        """Provide a formatted string representation for logger.infoing."""
        return json.dumps(self.to_dict(), indent=4)

    def show(self, message: Optional[str] = None) -> None:
        """
        Display the current configuration in a formatted manner.

        Args:
            message (Optional[str]): Message to display before showing the configuration.
        """
        logger.info(message if message else "Current configuration:")
        logger.info(make_bar())
        logger.info(self)  # Use the __str__ method for formatted output
        logger.info(make_bar())


def _get_user_port_choice(prompt: str, default_port: int) -> int:
    """Helper to get port choice from user with validation."""
    result = _get_yes_no_input(
        prompt=prompt, default_choice="y", accept_value={"port": int}
    )

    if result is True:
        return default_port
    elif result is False:
        raise ValueError("Port selection aborted by user")
    else:  # port number
        if is_port_available(result):
            return result
        logger.warning(f"Port {result} is not available, please try again")
        return _get_user_port_choice(prompt, default_port)


def _get_yes_no_input(
    prompt: str,
    default_choice: str = "y",
    accept_value: Optional[dict[str, type]] = None,
) -> Union[bool, Any]:
    """General helper to get yes/no or specific value input from user.

    Args:
        prompt (str): The prompt to display
        default_choice (str): Default choice if user just presses enter
        accept_value (Optional[dict]): If provided, allows user to input a specific value.
            Should be a dict with single key-value pair like {"port": int}

    Returns:
        Union[bool, Any]: True/False for yes/no, or the accepted value if provided
    """
    while True:
        choice = input(prompt).strip().lower()

        # Handle empty input
        if not choice:
            choice = default_choice

        # Handle yes/no
        if not accept_value:
            if choice in ("y", "yes"):
                return True
            if choice in ("n", "no"):
                return False
            logger.info("Invalid input, please enter Y/n")
            continue

        # Handle value input
        if accept_value:
            if len(accept_value) != 1:
                raise ValueError(
                    "accept_value should contain exactly one key-value pair"
                )

            key, value_type = next(iter(accept_value.items()))
            if choice in ("y", "yes"):
                return True
            if choice in ("n", "no"):
                return False

            try:
                return value_type(choice)
            except ValueError:
                logger.info(f"Invalid input, please enter Y/n or a valid {key}")


def _get_yes_no_input_with_timeout(
    prompt: str,
    default_choice: str = "y",
    accept_value: Optional[dict[str, type]] = None,
    timeout=30,
):
    """Get yes/no input with timeout.

    Args:
        prompt: Input prompt string
        timeout: Timeout in seconds
        default: Default value to return if timeout occurs (None means raise TimeoutError)

    Returns:
        bool: True for yes, False for no
    Raises:
        TimeoutError: If timeout occurs and no default is provided
    """
    result = None

    def input_thread():
        nonlocal result
        try:
            result = _get_yes_no_input(prompt, default_choice, accept_value)
        except Exception:
            pass

    thread = threading.Thread(target=input_thread)
    thread.daemon = True
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        if default_choice is not None:
            return default_choice
        raise TimeoutError("Input timed out")
    return result


def _get_valid_username(username: str = "") -> str:
    """
    Helper to get a valid username through interactive input.
    Ensures username is not empty, contains no whitespace, and is not 'cels'.

    Args:
        existing_username (str): Pre-existing username to validate

    Returns:
        str: Validated username
    """

    is_valid = False
    while not is_valid:
        username = (
            username.strip().lower()
            if username
            else input("Enter your username: ").strip()
        )

        if not username:
            logger.warning("Username cannot be empty.")
            username = ""
            continue
        if " " in username:
            logger.warning("Invalid username: Must not contain spaces.")
            username = ""
            continue
        if username.lower() == "cels":
            logger.warning("Invalid username: 'cels' is not allowed.")
            username = ""
            continue

        is_valid = True

    return username


def save_config(
    config_data: ArgoConfig, config_path: Optional[str | Path] = None
) -> str:
    """Save configuration to YAML file.

    Args:
        config_data: The ArgoConfig instance to save
        config_path: Optional path to save the config. If not provided,
            will use default path in user's config directory.

    Returns:
        str: The path where the config was saved

    Raises:
        OSError: If there are issues creating directories or writing the file
    """
    if config_path is None:
        home_dir = os.getenv("HOME") or os.path.expanduser("~")
        config_path = os.path.join(home_dir, ".config", "argoproxy", "config.yaml")

    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w") as f:
        yaml.dump(config_data.to_dict(), f)

    return str(config_path)


def create_config() -> ArgoConfig:
    """Interactive method to create and persist config."""
    logger.info("Creating new configuration...")

    random_port = get_random_port(49152, 65535)
    config_data = ArgoConfig(
        port=_get_user_port_choice(
            prompt=f"Use port [{random_port}]? [Y/n/<port>]: ",
            default_port=random_port,
        ),
        user=_get_valid_username(),
        verbose=_get_yes_no_input(prompt="Enable verbose mode? [Y/n] "),
    )

    config_path = save_config(config_data)
    logger.info(f"Created new configuration at: {config_path}")

    return config_data


def _apply_env_overrides(config_data: ArgoConfig) -> ArgoConfig:
    """Apply environment variable overrides to the config"""
    if env_port := os.getenv("PORT"):
        config_data.port = int(env_port)
    if env_verbose := os.getenv("VERBOSE"):
        config_data.verbose = env_verbose.lower() in ["true", "1", "t"]
    return config_data


def load_config(
    optional_path: Optional[str | Path] = None,
    *,
    env_override: bool = True,
    verbose: bool = True,
) -> Tuple[Optional[ArgoConfig], Optional[Path]]:
    """Loads configuration from file with optional environment variable overrides.

    Returns both the loaded config and the actual path it was loaded from.
    Assumes configuration is already validated.

    Args:
        optional_path: Optional path to a specific configuration file to load. If not provided,
            will attempt to load from default locations defined in PATHS_TO_TRY.
        env_override: If True, environment variables will override the configuration file settings. Defaults to True.
        verbose: If True, will print verbose output. Defaults to True.

    Returns:
        Tuple[Optional[ArgoConfig], Optional[Path]]:
            - Tuple containing (loaded_config, actual_path) if successful
            - None if no valid configuration file could be loaded or if loading failed

    Notes:
        - If a configuration is successfully loaded, environment variables will override
          the file-based configuration.
        - Returns None, None if loading fails for any reason
    """
    paths_to_try = [str(optional_path)] if optional_path else [] + PATHS_TO_TRY

    for path in paths_to_try:
        if path and os.path.exists(path):
            with open(path, "r") as f:
                try:
                    config_dict = yaml.safe_load(f)
                    config_data = ArgoConfig.from_dict(config_dict)
                    if env_override:
                        config_data = _apply_env_overrides(config_data)
                    actual_path = Path(path).absolute()
                    if verbose:
                        logger.info(f"Loaded configuration from {actual_path}")
                    return config_data, actual_path
                except (yaml.YAMLError, AssertionError) as e:
                    logger.warning(f"Error loading config at {path}: {e}")
                    continue

    return None, None


def validate_config(
    optional_path: Optional[str] = None, show_config: bool = False
) -> ArgoConfig:
    """Validate configuration with user interaction if needed"""
    config_data, actual_path = load_config(optional_path)

    if not config_data:
        logger.error("No valid configuration found.")
        user_decision = _get_yes_no_input(
            "Would you like to create it from config.sample.yaml? [Y/n]: "
        )
        if user_decision:
            config_data = create_config()
            show_config = True
        else:
            logger.warning("User aborted configuration creation. Exiting...")
            exit(1)

    # Config may change here. We need to persist
    file_changed = config_data.validate()
    if file_changed:
        config_original, _ = load_config(actual_path, env_override=False, verbose=False)
        if not config_original:
            raise ValueError("Failed to load original configuration for comparison.")
        # prompt user with yes or no to ask for persistence of changes
        logger.info("Configuration has been modified.")
        config_original.show("Original configuration:")
        config_data.show("Current Configuration:")
        user_decision = _get_yes_no_input(
            "Do you want to save the changes to the configuration file? [y/N]: ",
            default_choice="n",
        )
        if user_decision:
            save_config(config_data, actual_path)

    if show_config:
        config_data.show()

    return config_data
