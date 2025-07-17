# Basic Usage

This section covers the fundamental aspects of using Argo Proxy, from configuration to advanced features.

## Quick Navigation

```{toctree}
:maxdepth: 2

configuration
running
streaming
cli
endpoints
models
```

## Overview

Argo Proxy provides a comprehensive OpenAI-compatible interface to the ARGO API system. The basic usage workflow involves:

1. **[Configuration](configuration.md)** - Set up your config file with API endpoints and preferences
2. **[Running](running.md)** - Start the proxy server and perform first-time setup
3. **[Understanding Endpoints](endpoints.md)** - Learn about available API endpoints
4. **[Model Selection](models.md)** - Choose from available chat and embedding models
5. **[Advanced Features](streaming.md)** - Configure streaming modes and other advanced options

## Getting Started

If you're new to Argo Proxy, we recommend following this order:

1. Start with [Configuration](configuration.md) to understand the config file structure
2. Learn how to [run the application](running.md) and complete first-time setup
3. Explore the available [endpoints](endpoints.md) for your use case
4. Choose appropriate [models](models.md) for your tasks
5. Configure [streaming modes](streaming.md) based on your needs
6. Use [CLI options](cli.md) for advanced control
7. Explore [advanced features](../advanced/index.md) like tool calls for function calling capabilities

## Quick Reference

- **Default Port**: Randomly assigned (can be configured)
- **Config File Locations**: `./config.yaml`, `~/.config/argoproxy/config.yaml`, `~/.argoproxy/config.yaml`
- **Health Check**: `GET /health`
- **Version Info**: `GET /version`
- **OpenAI Compatible**: `/v1/chat/completions`, `/v1/embeddings`, `/v1/models`
