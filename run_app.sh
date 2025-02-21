#!/bin/bash

# Function to extract value from YAML for a given key
get_yaml_value() {
    local key="$1"
    local config="$2"
    echo "$config" | grep "$key" | awk '{print $2}'
}

# Read configuration from YAML file if it exists
yaml_port=""
yaml_argo_url=""
yaml_user=""
yaml_verbose=""
yaml_num_workers=""
yaml_timeout=""

if [ -f "config.yaml" ]; then
    config=$(cat config.yaml)
    yaml_port=$(get_yaml_value "port" "$config")
    yaml_argo_url=$(get_yaml_value "argo_url" "$config")
    yaml_user=$(get_yaml_value "user" "$config")
    yaml_verbose=$(get_yaml_value "verbose" "$config")
    yaml_num_workers=$(get_yaml_value "num_workers" "$config")
    yaml_timeout=$(get_yaml_value "timeout" "$config")
fi

# Determine final values, using environment variables if set
final_port=${PORT:-$yaml_port}
final_argo_url=${ARGO_URL:-$yaml_argo_url}
final_user=$yaml_user # don't read from system for final_user
final_verbose=${VERBOSE:-$yaml_verbose}
final_num_workers=${NUM_WORKERS:-$yaml_num_workers}
final_timeout=${TIMEOUT:-$yaml_timeout}

# Set default values if variables are still empty
final_port=${final_port:-8000}
final_argo_url=${final_argo_url:-"default_argo_url"}
final_user=${final_user:-"cels"}
final_verbose=${final_verbose:-"false"}
final_num_workers=${final_num_workers:-4}
final_timeout=${final_timeout:-30}

# Run the app locally with Gunicorn
echo "Starting app on port $final_port with ARGO_URL=$final_argo_url, USER=$final_user, VERBOSE=$final_verbose, NUM_WORKERS=$final_num_workers, and TIMEOUT=$final_timeout"
gunicorn -b 0.0.0.0:$final_port -w $final_num_workers --timeout $final_timeout app:app
