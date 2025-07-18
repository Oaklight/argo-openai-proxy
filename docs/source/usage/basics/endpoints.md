# API Endpoints

Argo Proxy provides multiple types of endpoints to accommodate different use cases and compatibility requirements.

Here we assume the service is running on `localhost:44497`. You should replace it with your actual service address.

## OpenAI Compatible Endpoints

These endpoints convert responses from the ARGO API to be compatible with OpenAI's format, allowing you to use existing OpenAI client libraries and tools.

### `/v1/chat/completions`

Chat Completions API - the primary endpoint for conversational AI.

```bash
POST http://localhost:44497/v1/chat/completions
```

### `/v1/completions`

Legacy Completions API for text completion tasks.

```bash
POST http://localhost:44497/v1/completions
```

**Note**: This is the legacy format. Use `/v1/chat/completions` for new applications.

### `/v1/embeddings`

Embedding API for generating text embeddings.

```bash
POST http://localhost:44497/v1/embeddings
```

### `/v1/responses`

**Available from**: v2.7.0

Response API - OpenAI's next generation API endpoint for handling response-based interactions. Experimental, use with caution.

```bash
POST http://localhost:44497/v1/responses
```

### `/v1/models`

Lists available models in OpenAI-compatible format.

```bash
GET http://localhost:44497/v1/models
```

**Response**: Returns a list of available chat and embedding models with OpenAI-compatible naming.

## Direct ARGO API Endpoints

These endpoints interact directly with the ARGO API and do not convert responses to OpenAI's format. Use these when you need direct access to ARGO-specific features or response formats.

### `/v1/chat`

Proxies requests to the ARGO API without conversion.

```bash
POST http://localhost:44497/v1/chat
```

### `/v1/embed`

Proxies requests to the ARGO Embedding API without conversion.

```bash
POST http://localhost:44497/v1/embed
```

## Utility Endpoints

### `/health`

Health check endpoint for monitoring and load balancing.

```bash
GET http://localhost:44497/health
```

**Response**: Returns `200 OK` if the server is running properly.

**Use cases:**

- Service discovery

### `/version`

**Available from**: v2.7.0.post1

Returns version information and update notifications.

```bash
GET http://localhost:44497/version
```

**Response**:

- Current ArgoProxy version
- Notification if a new version is available
- Version comparison information

## Timeout Override

All endpoints support timeout override through a `timeout` parameter in your request. This parameter is optional for client requests, and the proxy server will keep the connection open until it finishes or the client disconnects.

### Usage Examples

**JSON Body:**

```json
{
  "model": "argo:gpt-4",
  "messages": [...],
  "timeout": 120
}
```

**Query Parameter:**

```bash
POST /v1/chat/completions?timeout=120
```

For detailed examples of timeout override in different request formats, see [Timeout Override Examples](timeout_examples).

## Endpoint Selection Guide

### Use OpenAI Compatible Endpoints When

- Migrating from OpenAI API
- Using existing OpenAI client libraries
- Need standardized response formats
- Building applications with OpenAI ecosystem tools

### Use Direct ARGO Endpoints When

- Need ARGO-specific features
- Require native ARGO response formats
- Building custom integrations
- Performance optimization for ARGO-native workflows

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (authentication issues)
- **429**: Too Many Requests (rate limiting)
- **500**: Internal Server Error
- **502**: Bad Gateway (upstream API issues)
- **503**: Service Unavailable (server overloaded)
