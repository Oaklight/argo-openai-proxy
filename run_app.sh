#!/bin/bash

# Default configuration
PORT=6000
ARGO_URL="https://apps-dev.inside.anl.gov/argoapi/api/v1/resource/chat/"
USER="cels"
VERBOSE=false
NUM_WORKERS=4

# Read configuration from YAML file if it exists
if [ -f "config.yaml" ]; then
    CONFIG=$(cat config.yaml)
    PORT=$(echo "$CONFIG" | grep port | awk '{print $2}')
    ARGO_URL=$(echo "$CONFIG" | grep argo_url | awk '{print $2}')
    USER=$(echo "$CONFIG" | grep user | awk '{print $2}')
    VERBOSE=$(echo "$CONFIG" | grep verbose | awk '{print $2}')
    NUM_WORKERS=$(echo "$CONFIG" | grep num_workers | awk '{print $2}')
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
        -e VERBOSE=$VERBOSE \
        argo-proxy
else
    # Run the app locally with Gunicorn
    echo "Starting app on port $PORT with ARGO_URL=$ARGO_URL, USER=$USER, VERBOSE=$VERBOSE, and NUM_WORKERS=$NUM_WORKERS"
    gunicorn -b 0.0.0.0:$PORT -w $NUM_WORKERS app:app
fi
