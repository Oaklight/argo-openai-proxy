# Streaming Modes

Argo Proxy supports two streaming modes for Chat Completions, Legacy Completions and Responses endpoints. Each mode has its own advantages and use cases. This guide explains the differences between the two modes and helps you choose the right one for your needs.

Why use stream mode?
Some applications - llm clients, IDE extensions (like cline, continue.dev) and many chat-based tools—require stream mode to function correctly. Stream mode also allows you to create apps that provide a "flowing" feeling, letting users see responses generated word-by-word or line-by-line in real time, rather than waiting for the full output. This can greatly improve the responsiveness and perceived performance of your application.

## Pseudo Stream (Default, Recommended)

- **Default behavior**: Enabled by default (omitted or `real_stream: false` in config)
- **How it works**: Receives the complete response from upstream, then simulates streaming by sending chunks to the client
- **Status**: Production-ready and stable

### Advantages

- More stable and reliable experience
- Better error handling and recovery
- Consistent performance
- **Recommended for production use**

### Disadvantages

- "Hard task" for LLM may take longer to start streaming

### Configuration

**Via config file:**

```yaml
# Simply omit the setting (defaults to false)

# Or explicitly use pseudo streaming (default)
real_stream: false
```

**Via CLI:**

```bash
# Use default pseudo streaming
argo-proxy
```

## Real Stream (Experimental)

- **Enable via**: Set `real_stream: true` in config file or use `--real-stream`/`-rs` CLI flag
- **How it works**: Directly streams chunks from the upstream API as they arrive
- **Status**: Currently in testing phase

### When to Use

- Testing streaming performance
- Development environments
- When you need true real-time streaming behavior

### Known Issues

- Time to first token may vary. Sometimes it can be longer than pseudo stream.
- Ongoing stream may stall for a few seconds before resuming.

### Configuration

**Via config file:**

```yaml
# Explicitly enable real streaming (experimental)
real_stream: true
```

**Via CLI flag:**

```bash
# Enable real streaming for this session
argo-proxy --real-stream

# Or use the shorthand
argo-proxy -rs
```

### Feedback Welcome

We welcome feedback on real streaming performance and stability. Please report any issues or observations to help improve this feature by emailing Matthew Dearing AND Peng Ding.

## Function Calling Behavior

When using function calling (tool calls):

- **Pseudo stream is automatically enforced** regardless of your configuration
- This ensures reliable function call processing with the current prompting-based implementation
- Users will not notice this automatic switch as the experience remains smooth
- Native function calling support is work in progress (WIP)

## Choosing the Right Mode

### Use Pseudo Stream When

- Running in production environments
- Reliability is more important than minimal latency
- Using function calling features
- Network conditions are variable

### Use Real Stream When

- Testing streaming performance
- Running in controlled development environments
- Providing feedback on experimental features (Thank you!)

## Troubleshooting

### Common Issues

- **Streaming stops unexpectedly**: Switch to pseudo stream mode for more reliable results.
- **High latency in pseudo mode**: Normal behavior if your task is relatively hard for the model, or you require longer responses.
- **Connection timeouts in real mode**: Consider switching to pseudo stream for better reliability
