import logging
import os
import sys

import yaml

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
    "verbose",
    "num_workers",
    "timeout",
]

for key in required_keys:
    assert key in config, f"{config_path} is missing the '{key}' variable."

# Echo config to console
print("Configuration loaded successfully:")
print(config)
