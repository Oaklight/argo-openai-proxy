#!/bin/bash

# Function to extract value from YAML for a given key
get_yaml_value() {
    local key="$1"
    local config="$2"
    echo "$config" | grep "$key" | awk '{print $2}'
}

# Define the required configuration variables
required_vars=("port" "argo_url" "argo_embedding_url" "user" "verbose" "num_workers" "timeout")

# Check if config.yaml file exists
if [ ! -f "config.yaml" ]; then # Corrected: Added space after '['
    echo "Error: config.yaml file not found."
    exit 1
fi

# Check if the file contains all required variables
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var:" "config.yaml"; then
        echo "Error: config.yaml is missing the '$var' variable."
        exit 1
    fi
done

# Output success message if all checks pass
echo "config.yaml exists and contains all required variables."

# Load the entire config into a variable
config=$(cat config.yaml)

# Run the application
timeout=$(get_yaml_value "timeout" "$config")
port=$(get_yaml_value "port" "$config")
num_workers=$(get_yaml_value "num_workers" "$config")

gunicorn -b 0.0.0.0:$port -w $num_workers --timeout $timeout app:app
