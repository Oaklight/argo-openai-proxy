import yaml

# Read configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

assert "port" in config, "config.yaml is missing the 'port' variable."
assert "argo_url" in config, "config.yaml is missing the 'argo_url' variable."
assert (
    "argo_embedding_url" in config
), "config.yaml is missing the 'argo_embedding_url' variable."
assert "user" in config, "config.yaml is missing the 'user' variable."
assert "verbose" in config, "config.yaml is missing the 'verbose' variable."
assert "num_workers" in config, "config.yaml is missing the 'num_workers' variable."
assert "timeout" in config, "config.yaml is missing the 'timeout' variable."
