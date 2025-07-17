# CLI Options

The Argo Proxy command-line interface provides comprehensive options for configuration, management, and operation.

## Command Syntax

```bash
argo-proxy [-h] [--host HOST] [--port PORT] [--verbose | --quiet] [--real-stream]
           [--edit] [--validate] [--show] [--version]
           [config]
```

## Positional Arguments

### config

Path to the configuration file.

```bash
argo-proxy /path/to/config.yaml
```

- **Optional**: If not provided, searches default locations
- **Fallback**: If specified file doesn't exist, falls back to default search

## Optional Arguments

### Help and Information

#### `-h, --help`

Show help message and exit.

```bash
argo-proxy --help
```

#### `--version, -V`

Show the version and exit.

```bash
argo-proxy --version
```

### Server Configuration

#### `--host HOST, -H HOST`

Host address to bind the server to.

```bash
argo-proxy --host 127.0.0.1
argo-proxy -H 0.0.0.0
```

- **Default**: Uses value from config file or `0.0.0.0`
- **Override**: Command-line value takes precedence over config file

#### `--port PORT, -p PORT`

Port number to bind the server to.

```bash
argo-proxy --port 8080
argo-proxy -p 44497
```

- **Default**: Uses value from config file or random available port
- **Override**: Command-line value takes precedence over config file

### Logging Control

#### `--verbose, -v`

Enable verbose logging.

```bash
argo-proxy --verbose
argo-proxy -v
```

- **Override**: Enables verbose logging even if `verbose: false` in config
- **Mutually exclusive**: Cannot be used with `--quiet`

#### `--quiet, -q`

Disable verbose logging.

```bash
argo-proxy --quiet
argo-proxy -q
```

- **Override**: Disables verbose logging even if `verbose: true` in config
- **Mutually exclusive**: Cannot be used with `--verbose`

### Streaming Configuration

#### `--real-stream, -rs`

Enable real streaming mode.

```bash
argo-proxy --real-stream
argo-proxy -rs
```

- **Override**: Enables real streaming even if `real_stream: false` or omitted in config
- **Experimental**: This feature is currently in testing phase

### Configuration Management

#### `--edit, -e`

Open the configuration file in the system's default editor.

```bash
argo-proxy --edit
argo-proxy -e
```

- **Search**: If no config file specified, searches default locations
- **Editors**: Tries common editors (nano, vi, vim on Unix; notepad on Windows)
- **No server start**: Only opens editor, doesn't start the proxy server

#### `--validate, -vv`

Validate the configuration file and exit.

```bash
argo-proxy --validate
argo-proxy -vv
```

- **Validation**: Checks config syntax and connectivity
- **No server start**: Exits after validation without starting server
- **Useful for**: Deployment scripts and configuration testing

#### `--show, -s`

Show the current configuration during launch.

```bash
argo-proxy --show
argo-proxy -s
```

- **Display**: Shows fully resolved configuration including defaults
- **Combination**: Can be used with `--validate` to display without starting server

## Usage Examples

### Basic Usage

```bash
# Start with default configuration
argo-proxy

# Start with specific config file
argo-proxy /path/to/config.yaml

# Start with custom host and port
argo-proxy --host 127.0.0.1 --port 8080
```

### Configuration Management

```bash
# Edit configuration file
argo-proxy --edit

# Validate configuration
argo-proxy --validate

# Show configuration and validate
argo-proxy --validate --show

# Show configuration at startup
argo-proxy --show
```

### Logging and Debugging

```bash
# Enable verbose logging
argo-proxy --verbose

# Disable verbose logging
argo-proxy --quiet

# Verbose with custom port
argo-proxy --verbose --port 8080
```

### Experimental Features

```bash
# Enable real streaming
argo-proxy --real-stream

# Real streaming with verbose logging
argo-proxy --real-stream --verbose
```

### Combined Options

```bash
# Custom host, port, and verbose logging
argo-proxy --host 0.0.0.0 --port 44497 --verbose

# Validate specific config with display
argo-proxy /path/to/config.yaml --validate --show

# Edit config for specific file
argo-proxy /path/to/config.yaml --edit
```

## Configuration Precedence

Command-line options override configuration file values in this order:

1. **Command-line arguments** (highest priority)
2. **Configuration file values**
3. **Default values** (lowest priority)

## Exit Codes

- **0**: Success
- **1**: General error (configuration, network, etc.)
- **2**: Invalid command-line arguments

## Tips

### Quick Configuration Check

```bash
# Quick way to check if config is valid
argo-proxy --validate && echo "Config is valid"
```

### Development Workflow

```bash
# Edit config, validate, then run
argo-proxy --edit
argo-proxy --validate
argo-proxy --verbose
```

### Production Deployment

```bash
# Validate before deployment
argo-proxy --validate /etc/argoproxy/config.yaml

# Run in production
argo-proxy /etc/argoproxy/config.yaml --quiet
```
