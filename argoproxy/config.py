import os
import sys

import yaml

from sanic.log import logger

# Get the config path from the environment variable, default to 'config.yaml' if not set
config_path = os.getenv("CONFIG_PATH", "config.yaml")
# Read configuration from YAML file
try:
    with open(config_path, "r") as file:
        config = yaml.safe_load(file)
    logger.info("Configuration loaded successfully.")
except FileNotFoundError:
    logger.error("Configuration file 'config.yaml' not found.")
    sys.exit(1)
except yaml.YAMLError as e:
    logger.error(f"Error parsing configuration file: {e}")
    sys.exit(1)

# Ensure all required keys are present in the config
required_keys = [
    "port",
    "argo_url",
    "argo_embedding_url",
    "user",
    "num_workers",
    "timeout",
]

for key in required_keys:
    assert key in config, f"{config_path} is missing the '{key}' variable."

verbose = os.getenv("VERBOSE", config.get("verbose", False))
config["verbose"] = verbose
logging_level = os.getenv("LOG_LEVEL", config.get("logging_level", "INFO"))

if verbose:
    config["logging_level"] = "DEBUG"
else:
    config["logging_level"] = logging_level

# Echo config to console
logger.debug("Configuration loaded successfully:")
logger.debug(config)
