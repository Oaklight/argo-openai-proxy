#!/bin/bash

# Default configuration
PORT=6000
ARGO_URL="https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
USER="cels"

# Read configuration from YAML file if it exists
if [ -f "config.yaml" ]; then
    CONFIG=$(cat config.yaml)
    PORT=$(echo "$CONFIG" | grep port | awk '{print $2}')
    ARGO_URL=$(echo "$CONFIG" | grep argo_url | awk '{print $2}')
    USER=$(echo "$CONFIG" | grep user | awk '{print $2}')
fi

# Start the app in Docker or locally
if [ "$1" == "docker" ]; then
    # Build the Docker image
    docker build -t argo-proxy .

    # Run the Docker container
    docker run -d -p $PORT:$PORT --name argo-proxy-container \
        -e PORT=$PORT \
        -e ARGO_URL=$ARGO_URL \
        -e USER=$USER \
        argo-proxy
else
    # Run the app locally
    echo "Starting app on port $PORT with ARGO_URL=$ARGO_URL and USER=$USER"
    export PORT=$PORT
    export ARGO_URL=$ARGO_URL
    export USER=$USER
    python3 app.py
fi
