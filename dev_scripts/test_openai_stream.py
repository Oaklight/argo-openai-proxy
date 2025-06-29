#!/usr/bin/env python3

import json
from argoproxy.tool_calls.output_handle import tool_calls_to_openai_stream
from argoproxy.types.chat_completion import (
    ChatCompletionChunk,
    StreamChoice,
    ChoiceDelta,
)

# 测试工具调用转换
tool_calls_flow = [{"name": "add", "arguments": {"a": 8, "b": 5}}]
openai_tool_calls = [tool_calls_to_openai_stream(tc) for tc in tool_calls_flow]

print("OpenAI tool calls for streaming:")
for tc in openai_tool_calls:
    print(json.dumps(tc.model_dump(), indent=2))

# 创建一个包含工具调用的流式响应
chunk = ChatCompletionChunk(
    id="test_id",
    created=1234567890,
    model="test_model",
    choices=[
        StreamChoice(
            index=0,
            delta=ChoiceDelta(tool_calls=openai_tool_calls),
            finish_reason="tool_calls",
        )
    ],
)

print("\nComplete streaming chunk with tool calls:")
print(json.dumps(chunk.model_dump(), indent=2))
