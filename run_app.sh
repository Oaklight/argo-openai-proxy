#!/bin/bash

# Function to extract value from YAML for a given key
get_yaml_value() {
    local key="$1"
    local config="$2"
    echo "$config" | grep "$key" | awk '{print $2}'
}

# Default config path
CONFIG_PATH=${1:-"config.yaml"}

# Export the config path as an environment variable
export CONFIG_PATH

# Check if config.yaml file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "Error: $CONFIG_PATH file not found."
    exit 1
fi

# Define the required configuration variables
required_vars=("port" "argo_url" "argo_embedding_url" "user" "verbose" "num_workers" "timeout")

# Check if the file contains all required variables
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var:" "$CONFIG_PATH"; then
        echo "Error: $CONFIG_PATH is missing the '$var' variable."
        exit 1
    fi
done

# Output success message if all checks pass
echo "$CONFIG_PATH exists and contains all required variables."

# Load the entire config into a variable
config=$(cat "$CONFIG_PATH")

# Run the application
timeout=$(get_yaml_value "timeout" "$config")
port=$(get_yaml_value "port" "$config")
num_workers=$(get_yaml_value "num_workers" "$config")

gunicorn -b 0.0.0.0:$port -w $num_workers --timeout $timeout app:app
