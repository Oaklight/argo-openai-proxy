#!/bin/bash

# Default config path
CONFIG_PATH=${1:-"config.yaml"}

# Check if config.yaml file exists
if [ ! -f "$CONFIG_PATH" ]; then
    echo "$CONFIG_PATH file not found."
    read -p "Would you like to create it from config.sample.yaml? [y/N] " create_config
    if [[ "$create_config" =~ ^[Yy]$ ]]; then
        cp config.sample.yaml "$CONFIG_PATH"

        # Prompt for username
        read -p "Enter your username: " username
        sed -i "s/^user:.*/user: \"$username\"/" "$CONFIG_PATH"

        # Prompt for verbose mode
        read -p "Enable verbose mode? [Y/n] " verbose
        if [[ "$verbose" =~ ^[Nn]$ ]]; then
            sed -i "s/^verbose:.*/verbose: false/" "$CONFIG_PATH"
        fi

        echo "Created $CONFIG_PATH with your settings:"
        echo "--------------------------------------"
        cat "$CONFIG_PATH"
        echo "--------------------------------------"
        read -p "Review the config above. Press enter to continue or Ctrl+C to abort."
    else
        echo "Aborting: config file required."
        exit 1
    fi
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

# Load the port and num_workers from the config
port=$(grep "^port:" "$CONFIG_PATH" | awk '{print $2}')
num_workers=$(grep "^num_workers:" "$CONFIG_PATH" | awk '{print $2}')

# Run the application using Sanic's built-in server
sanic app:app --host=0.0.0.0 --port=$port --workers=$num_workers
