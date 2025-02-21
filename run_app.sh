#!/bin/bash

# Function to extract value from YAML for a given key
get_yaml_value() {
    local key="$1"
    local config="$2"
    echo "$config" | grep "$key" | awk '{print $2}'
}

# 定义需要检查的配置项
required_vars=("port" "argo_url" "argo_embedding_url" "user" "verbose" "num_workers" "timeout")

# 检查 config.yaml 文件是否存在
if [! -f "config.yaml" ]; then
    echo "Error: config.yaml file not found."
    exit 1
fi

# 检查文件中是否包含所有必需的变量
for var in "${required_vars[@]}"; do
    if ! grep -q "^$var:" "config.yaml"; then
        echo "Error: config.yaml is missing the '$var' variable."
        exit 1
    fi
done

# 输出检查通过的信息
echo "config.yaml exists and contains all required variables."

# 运行应用
timeout=$(get_yaml_value "timeout" "$config")
port=$(get_yaml_value "port" "$config")
num_workers=$(get_yaml_value "num_workers" "$config")

gunicorn -b 0.0.0.0:$port -w $num_workers --timeout $timeout app:app
