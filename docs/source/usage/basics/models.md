# Available Models

Argo Proxy provides access to various AI models through the ARGO API, with OpenAI-compatible naming conventions for easy integration.

## Chat Models

### OpenAI Series

The OpenAI model series includes various GPT models with different capabilities and context lengths.

| Original ARGO Model Name | Argo Proxy Name                          | Description                    |
| ------------------------ | ---------------------------------------- | ------------------------------ |
| `gpt35`                  | `argo:gpt-3.5-turbo`                     | GPT-3.5 Turbo                  |
| `gpt35large`             | `argo:gpt-3.5-turbo-16k`                 | GPT-3.5 Turbo with 16K context |
| `gpt4`                   | `argo:gpt-4`                             | GPT-4 base model               |
| `gpt4large`              | `argo:gpt-4-32k`                         | GPT-4 with 32K context         |
| `gpt4turbo`              | `argo:gpt-4-turbo`                       | GPT-4 Turbo                    |
| `gpt4o`                  | `argo:gpt-4o`                            | GPT-4o                         |
| `gpt4olatest`            | `argo:gpt-4o-latest`                     | Latest GPT-4o version          |
| `gpto1preview`           | `argo:gpt-o1-preview`, `argo:o1-preview` | GPT-o1 Preview                 |
| `gpto1mini`              | `argo:gpt-o1-mini`, `argo:o1-mini`       | GPT-o1 Mini                    |
| `gpto3mini`              | `argo:gpt-o3-mini`, `argo:o3-mini`       | GPT-o3 Mini                    |
| `gpto1`                  | `argo:gpt-o1`, `argo:o1`                 | GPT-o1                         |
| `gpto3`                  | `argo:gpt-o3`, `argo:o3`                 | GPT-o3                         |
| `gpto4mini`              | `argo:gpt-o4-mini`, `argo:o4-mini`       | GPT-o4 Mini                    |
| `gpt41`                  | `argo:gpt-4.1`                           | GPT-4.1                        |
| `gpt41mini`              | `argo:gpt-4.1-mini`                      | GPT-4.1 Mini                   |
| `gpt41nano`              | `argo:gpt-4.1-nano`                      | GPT-4.1 Nano                   |

### Google Gemini Series

Google's Gemini models offer advanced multimodal capabilities.

| Original ARGO Model Name | Argo Proxy Name         | Description      |
| ------------------------ | ----------------------- | ---------------- |
| `gemini25pro`            | `argo:gemini-2.5-pro`   | Gemini 2.5 Pro   |
| `gemini25flash`          | `argo:gemini-2.5-flash` | Gemini 2.5 Flash |

### Anthropic Claude Series

Anthropic's Claude models are known for their safety and reasoning capabilities.

| Original ARGO Model Name | Argo Proxy Name                                    | Description       |
| ------------------------ | -------------------------------------------------- | ----------------- |
| `claudeopus4`            | `argo:claude-opus-4`, `argo:claude-4-opus`         | Claude Opus 4     |
| `claudesonnet4`          | `argo:claude-sonnet-4`, `argo:claude-4-sonnet`     | Claude Sonnet 4   |
| `claudesonnet37`         | `argo:claude-sonnet-3.7`, `argo:claude-3.7-sonnet` | Claude Sonnet 3.7 |
| `claudesonnet35v2`       | `argo:claude-sonnet-3.5`, `argo:claude-3.5-sonnet` | Claude Sonnet 3.5 |

## Embedding Models

Embedding models convert text into numerical vectors for similarity search, clustering, and other ML tasks.

| Original ARGO Model Name | Argo Proxy Name               | Description                   |
| ------------------------ | ----------------------------- | ----------------------------- |
| `ada002`                 | `argo:text-embedding-ada-002` | OpenAI Ada 002 embeddings     |
| `v3small`                | `argo:text-embedding-3-small` | OpenAI text-embedding-3-small |
| `v3large`                | `argo:text-embedding-3-large` | OpenAI text-embedding-3-large |

## Model Selection Guide

### For General Chat Applications

**Recommended**: `argo:gpt-4o` or `argo:gpt-4-turbo`

- Good balance of performance and cost
- Suitable for most conversational AI applications
- Strong reasoning capabilities

### For Cost-Sensitive Applications

**Recommended**: `argo:gpt-3.5-turbo`

- Lower cost per token
- Good performance for simpler tasks
- Faster response times

### For Complex Reasoning Tasks

**Recommended**: `argo:gpt-o1` or `argo:claude-4-sonnet`

- Advanced reasoning capabilities
- Better for complex problem-solving
- Higher accuracy on difficult tasks

### For Large Context Requirements

**Recommended**: `argo:gpt-4-32k` or `argo:gpt-3.5-turbo-16k`

- Extended context windows
- Suitable for long document processing
- Better for complex conversations

### For Embeddings

**Text Similarity**: `argo:text-embedding-3-large`

- Highest quality embeddings
- Best for semantic search

**Cost-Effective Embeddings**: `argo:text-embedding-3-small`

- Good quality with lower cost
- Suitable for most embedding tasks

## Usage Examples

### Chat Completion

```python
import openai

client = openai.OpenAI(
    base_url="http://localhost:44497/v1",
    api_key="dummy"  # Not used, but required by client
)

response = client.chat.completions.create(
    model="argo:gpt-4o",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)
```

### Embeddings

```python
response = client.embeddings.create(
    model="argo:text-embedding-3-large",
    input="Text to embed"
)
```

### Model Listing

```python
models = client.models.list()
for model in models.data:
    print(f"Model: {model.id}")
```

## Model Capabilities

### Function Calling Support

The following models support function calling (tool calls):

- All GPT-4 series models
- GPT-3.5-turbo series
- Claude series models
- Gemini series models

### Streaming Support

All chat models support both streaming and non-streaming responses:

- **Streaming**: Real-time token generation
- **Non-streaming**: Complete response delivery

### Context Limits

| Model Series   | Typical Context Length            |
| -------------- | --------------------------------- |
| GPT-3.5        | 4K tokens (16K for large variant) |
| GPT-4          | 8K tokens (32K for large variant) |
| GPT-4 Turbo/4o | 128K tokens                       |
| GPT-o1 series  | 128K tokens                       |
| Claude series  | 200K tokens                       |
| Gemini series  | 1M tokens                         |

## Model Availability

Model availability may vary based on:

- ARGO API service status
- Regional restrictions
- Usage quotas
- Model deprecation schedules

Use the `/v1/models` endpoint to check current model availability:

```bash
curl http://localhost:44497/v1/models
```

## Performance Considerations

### Response Time

- **Fastest**: GPT-3.5-turbo, Gemini Flash
- **Balanced**: GPT-4o, GPT-4-turbo
- **Slower but higher quality**: GPT-o1, Claude Opus

### Cost Optimization

- Use smaller models for simple tasks
- Implement prompt caching where possible
- Consider context length requirements
- Monitor token usage patterns

### Quality vs Speed Trade-offs

- **High speed, good quality**: GPT-4o
- **Maximum quality**: GPT-o1, Claude Opus
- **Balanced**: GPT-4-turbo, Claude Sonnet
- **Cost-effective**: GPT-3.5-turbo

## Troubleshooting

### Model Not Available

If a model returns an error:

1. Check model name spelling
2. Verify model availability via `/v1/models`
3. Check ARGO API service status
4. Try alternative models in the same series

### Performance Issues

For slow responses:

1. Try a faster model variant
2. Reduce context length
3. Use streaming for better perceived performance
4. Check network connectivity to ARGO APIs
