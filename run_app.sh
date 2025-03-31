#!/bin/bash

# Default config path
CONFIG_PATH=${1:-"config.yaml"}

# Utility functions
validate_chat_api() {
    local url=$1
    local username=$2
    echo "Validating API endpoint: $url"

    payload=$(
        cat <<EOF
{
  "user": "$username",
  "model": "gpt4o",
  "messages": [
    {"role": "user", 
      "content": "What are you?"}
  ]
}
EOF
    )
    if ! curl --max-time 5 --fail -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1; then
        echo "Warning: Could not connect to API at $url"
        read -p "Continue anyway? [y/N] " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    return 0
}

validate_embedding_api() {
    local url=$1
    local username=$2
    echo "Testing embedding API at $url"

    payload=$(
        cat <<EOF
{
  "user": "$username",
  "model": "v3small",
  "prompt": [
    "hello"
  ]
}
EOF
    )
    if ! curl --max-time 5 --fail -X POST "$url" \
        -H "Content-Type: application/json" \
        -d "$payload" >/dev/null 2>&1; then
        echo "Warning: Could not connect to embedding API at $url"
        read -p "Continue anyway? [y/N] " choice
        if [[ ! "$choice" =~ ^[Yy]$ ]]; then
            return 1
        fi
    fi
    return 0
}

get_config_value() {
    local config_path=$1
    local key=$2
    grep "^$key:" "$config_path" | awk -F': ' '{print $2}' | sed -e 's/^"//' -e 's/"$//' -e "s/^'//" -e "s/'$//"
}

set_config_value() {
    local config_path=$1
    local key=$2
    local value=$3
    sed -i "s/^$key:.*/$key: $value/" "$config_path"
}

validate_port_number() {
    local port=$1
    [[ "$port" =~ ^[0-9]+$ ]] && [ "$port" -ge 1024 ] && [ "$port" -le 65535 ]
}

# Port management functions
check_port() {
    lsof -i :$1 >/dev/null 2>&1
}

get_available_port() {
    local port
    while true; do
        port=$((49152 + RANDOM % 16383))
        if ! check_port $port; then
            echo $port
            return
        fi
    done
}

handle_port_selection() {
    local current_port=$1
    if check_port $current_port; then
        echo "Port $current_port is already in use."
        local suggested_port=$(get_available_port)
        echo "Suggested available port: $suggested_port"

        read -p "Press enter to use $suggested_port or enter a different port: " new_port
        new_port=${new_port:-$suggested_port}

        if validate_port_number "$new_port"; then
            if ! check_port $new_port; then
                set_config_value "$CONFIG_PATH" "port" "$new_port"
                echo "Updated config with port $new_port"
                echo $new_port
                return
            else
                echo "Port $new_port is also in use."
            fi
        else
            echo "Invalid port number."
        fi

        echo "Aborting: No valid port selected."
        exit 1
    fi
    echo $current_port
}

# Display config with nice formatting
show_config() {
    local config_path=$1
    local message=$2
    echo "$message"
    echo "--------------------------------------"
    cat "$config_path"
    echo "--------------------------------------"
}

# Config file operations
create_config() {
    cp config.sample.yaml "$CONFIG_PATH"

    # Start with a random available port
    local port=$(get_available_port)
    read -p "Enter port [$port]: " new_port
    if [[ -n "$new_port" ]]; then
        port=$(handle_port_selection "$new_port")
    fi
    set_config_value "$CONFIG_PATH" "port" "$port"

    while true; do
        read -p "Enter your username: " username
        if [[ -z "$username" ]]; then
            echo "Error: Username cannot be empty"
        elif [[ "$username" == "cels" ]]; then
            echo "Error: 'cels' is not allowed as a username"
        else
            set_config_value "$CONFIG_PATH" "user" "\"$username\""
            break
        fi
    done

    read -p "Enable verbose mode? [Y/n] " verbose
    if [[ "$verbose" =~ ^[Nn]$ ]]; then
        set_config_value "$CONFIG_PATH" "verbose" "false"
    fi

    show_config "$CONFIG_PATH" "Created $CONFIG_PATH with your settings:"
    read -p "Review the config above. Press enter to continue or Ctrl+C to abort."
}

validate_config() {
    local config_path=$1
    local required_vars=("port" "argo_url" "argo_embedding_url" "user" "verbose" "num_workers" "timeout")
    local missing_vars=()
    local needs_fix=false

    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var:" "$config_path"; then
            missing_vars+=("$var")
            continue
        fi

        local value=$(get_config_value "$config_path" "$var")
        if [ -z "$value" ]; then
            needs_fix=true
            case "$var" in
            "port")
                local port=$(handle_port_selection $(get_available_port))
                set_config_value "$config_path" "port" "$port"
                ;;
            "user")
                while true; do
                    read -p "Please enter your username: " username
                    if [[ -z "$username" ]]; then
                        echo "Error: Username cannot be empty"
                    elif [[ "$username" == "cels" ]]; then
                        echo "Error: 'cels' is not allowed as a username"
                    else
                        set_config_value "$config_path" "user" "\"$username\""
                        break
                    fi
                done
                ;;
            "verbose")
                read -p "Enable verbose mode? [Y/n] " verbose
                if [[ "$verbose" =~ ^[Nn]$ ]]; then
                    set_config_value "$config_path" "verbose" "false"
                else
                    set_config_value "$config_path" "verbose" "true"
                fi
                ;;
            *)
                read -p "Please enter value for $var: " new_value
                set_config_value "$config_path" "$var" "\"$new_value\""
                ;;
            esac
        elif [ "$var" = "port" ] && check_port $value; then
            echo "Error: Configured port $value is already in use."
            return 1
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        echo "Error: Missing variables: ${missing_vars[*]}"
        return 1
    fi

    if $needs_fix; then
        show_config "$config_path" "Some values were empty and have been updated. Please review the config:"
        read -p "Press enter to continue or Ctrl+C to abort."
        # Re-validate after fixes
        validate_config "$config_path"
        return $?
    fi

    # Validate URLs
    local argo_url=$(get_config_value "$config_path" "argo_url")
    local argo_embedding_url=$(get_config_value "$config_path" "argo_embedding_url")
    local username=$(get_config_value "$config_path" "user")

    echo "Validating URL connectivity..."
    if ! validate_chat_api "$argo_url" "$username"; then
        return 1
    fi

    if ! validate_embedding_api "$argo_embedding_url" "$username"; then
        return 1
    fi

    return 0
}

# Main config file handling
if [ ! -f "$CONFIG_PATH" ]; then
    echo "$CONFIG_PATH file not found."
    read -p "Would you like to create it from config.sample.yaml? [y/N] " create_config
    if [[ "$create_config" =~ ^[Yy]$ ]]; then
        create_config
    else
        echo "Aborting: config file required."
        exit 1
    fi
fi

# Validate config file
if ! validate_config "$CONFIG_PATH"; then
    exit 1
fi

echo "$CONFIG_PATH exists and contains all required variables."

# Load the port and num_workers from the config
port=$(grep "^port:" "$CONFIG_PATH" | awk '{print $2}')
num_workers=$(grep "^num_workers:" "$CONFIG_PATH" | awk '{print $2}')

# Handle port selection
port=$(handle_port_selection $port)

# Run the application using Sanic's built-in server
sanic app:app --host=0.0.0.0 --port=$port --workers=$num_workers
