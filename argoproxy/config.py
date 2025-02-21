import os

import yaml

# Get the config path from the environment variable, default to 'config.yaml' if not set
config_path = os.getenv("CONFIG_PATH", "config.yaml")

# Read configuration from YAML file
with open(config_path, "r") as file:
    config = yaml.safe_load(file)

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
