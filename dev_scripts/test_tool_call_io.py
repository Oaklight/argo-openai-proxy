import asyncio

from argoproxy.tool_calls.input_handle import (
    handle_tools,
)
from argoproxy.tool_calls.output_handle import (
    ToolInterceptor,
    tool_calls_to_openai,
)


def test_handle_tools():
    """Test handle_tools function"""
    print("=== Testing handle_tools function ===")

    # Test data
    tools = [
        {
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression",
                    }
                },
                "required": ["expression"],
            },
        }
    ]

    # Test 1: Input with messages
    input_data_1 = {
        "messages": [{"role": "user", "content": "Calculate 2 + 3"}],
        "tools": tools,
        "tool_choice": "auto",
    }

    result_1 = handle_tools(input_data_1.copy())
    print("Test 1 - With messages:")
    print(f"System message length: {len(result_1['messages'][0]['content'])}")
    print(f"Tools field removed: {'tools' not in result_1}")

    # Test 2: Input with existing system message
    input_data_2 = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Calculate 2 + 3"},
        ],
        "tools": tools,
        "tool_choice": "auto",
    }

    result_2 = handle_tools(input_data_2.copy())
    print("\nTest 2 - With existing system message:")
    print(
        f"System message contains original content: {'You are a helpful assistant' in result_2['messages'][0]['content']}"
    )
    print(
        f"System message contains tool prompt: {'Available tools' in result_2['messages'][0]['content']}"
    )

    # Test 3: Input without tools
    input_data_3 = {"messages": [{"role": "user", "content": "Hello"}]}

    result_3 = handle_tools(input_data_3.copy())
    print("\nTest 3 - No tools:")
    print(f"Data unchanged: {result_3 == input_data_3}")


def test_tool_interceptor():
    """Test ToolInterceptor function"""
    print("\n=== Testing ToolInterceptor function ===")

    interceptor = ToolInterceptor()

    # Test 1: Single tool call
    response_1 = """<tool_call>
{
  "name": "calculate",
  "arguments": {"expression": "2 + 3"}
}
</tool_call>

The calculation result is 5."""

    tool_calls_1, remaining_1 = interceptor.process(response_1)
    print("Test 1 - Single tool call:")
    print(f"Parse successful: {tool_calls_1 is not None}")
    print(f"Tool name: {tool_calls_1[0]['name'] if tool_calls_1 else 'None'}")
    print(f"Tool arguments: {tool_calls_1[0]['arguments'] if tool_calls_1 else 'None'}")
    print(f"Remaining text: {remaining_1}")

    # Test 2: Multiple tool calls
    response_2 = """<tool_call>
{
  "name": "calculate",
  "arguments": {"expression": "2 + 3"}
}
</tool_call>

<tool_call>
{
  "name": "calculate", 
  "arguments": {"expression": "4 * 5"}
}
</tool_call>

Calculations complete."""

    tool_calls_2, remaining_2 = interceptor.process(response_2)
    print("\nTest 2 - Multiple tool calls:")
    print(f"Parse successful: {tool_calls_2 is not None}")
    print(f"Number of tool calls: {len(tool_calls_2) if tool_calls_2 else 0}")
    if tool_calls_2:
        for i, tc in enumerate(tool_calls_2):
            print(f"  Tool {i + 1}: name={tc.get('name')}, args={tc.get('arguments')}")

    # Test 3: No tool calls
    response_3 = "This is a regular response with no tool calls."

    tool_calls_3, remaining_3 = interceptor.process(response_3)
    print("\nTest 3 - No tool calls:")
    print(f"Correctly returns None: {tool_calls_3 is None}")
    print(f"Text unchanged: {remaining_3 == response_3}")

    # Test 4: Invalid JSON
    response_4 = """<tool_call>
{
  "name": "invalid",
  invalid json here
}
</tool_call>"""

    tool_calls_4, remaining_4 = interceptor.process(response_4)
    print("\nTest 4 - Invalid JSON:")
    print(f"Tool calls: {tool_calls_4}")
    print(f"Remaining text contains invalid marker: {'<invalid>' in remaining_4}")


def test_tool_interceptor_stream():
    """Test ToolInterceptor streaming functionality"""
    print("\n=== Testing ToolInterceptor streaming functionality ===")

    def test_sync_stream():
        """Test synchronous streaming"""
        print("\n--- Synchronous streaming tests ---")

        # Test 1: Basic streaming
        print("\nTest 1 - Basic sync stream:")
        interceptor = ToolInterceptor()
        chunks = [
            "Start text <tool_c",
            'all>{"name": "test", "arg',
            'uments": {"value": 42}}',
            "</tool_call> End text",
        ]

        results = []
        for tool_call, text in interceptor.process_stream(iter(chunks)):
            if tool_call:
                # Validate structure
                if "name" not in tool_call or "arguments" not in tool_call:
                    results.append(f"INVALID_TOOL: Missing fields in {tool_call}")
                else:
                    results.append(
                        f"TOOL: name={tool_call['name']}, args={tool_call['arguments']}"
                    )
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

        # Test 2: Multiple tool calls streaming
        print("\nTest 2 - Multiple tool calls sync stream:")
        interceptor = ToolInterceptor()
        chunks = [
            'First <tool_call>{"name": "first", "arguments": {}}',
            '</tool_call> Middle text <tool_call>{"name":',
            ' "second", "arguments": {}}</tool_call> Last text',
        ]

        results = []
        for tool_call, text in interceptor.process_stream(iter(chunks)):
            if tool_call:
                if "name" not in tool_call or "arguments" not in tool_call:
                    results.append(f"INVALID_TOOL: {tool_call}")
                else:
                    results.append(f"TOOL: {tool_call['name']}")
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

        # Test 3: Edge case - tag splitting
        print("\nTest 3 - Tag splitting sync stream:")
        interceptor = ToolInterceptor()
        chunks = [
            "<",
            "tool_",
            "call>",
            '{"name": "test", "arguments": {"value": 1}}',
            "<",
            "/tool_call>",
        ]

        results = []
        for tool_call, text in interceptor.process_stream(iter(chunks)):
            if tool_call:
                if "name" not in tool_call or "arguments" not in tool_call:
                    results.append(f"INVALID_TOOL: {tool_call}")
                else:
                    results.append(f"TOOL: {tool_call}")
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

        # Test 4: Invalid JSON handling
        print("\nTest 4 - Invalid JSON sync stream:")
        interceptor = ToolInterceptor()
        chunks = ['<tool_call>{"name": "invalid"', ", bad json syntax}</tool_call>"]

        results = []
        for tool_call, text in interceptor.process_stream(iter(chunks)):
            if tool_call:
                results.append(f"TOOL: {tool_call}")
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

    async def test_async_stream():
        """Test asynchronous streaming"""
        print("\n--- Asynchronous streaming tests ---")

        # Test 1: Basic async streaming
        print("\nTest 1 - Basic async stream:")
        interceptor = ToolInterceptor()

        async def async_chunks():
            chunks = [
                "Start text <tool_c",
                'all>{"name": "async_test", "arg',
                'uments": {"value": 100}}',
                "</tool_call> End text",
            ]
            for chunk in chunks:
                await asyncio.sleep(0.001)  # Simulate network delay
                yield chunk

        results = []
        async for tool_call, text in interceptor.process_stream(async_chunks()):
            if tool_call:
                if "name" not in tool_call or "arguments" not in tool_call:
                    results.append(f"INVALID_TOOL: Missing fields in {tool_call}")
                else:
                    results.append(
                        f"TOOL: name={tool_call['name']}, args={tool_call['arguments']}"
                    )
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

        # Test 2: Complex async stream - multiple tool calls
        print("\nTest 2 - Complex async stream:")
        interceptor = ToolInterceptor()

        async def complex_async_chunks():
            chunks = [
                "Analysis starting\n",
                '<tool_call>\n{"name": ',
                '"analyze", "arguments": ',
                '{"data": "sample"}}\n</tool_call>\n',
                "Analysis complete, starting calculation\n",
                '<tool_call>{"name": "calculate", ',
                '"arguments": {"expr": "2+2"}}</tool_call>\n',
                "All operations complete.",
            ]
            for chunk in chunks:
                await asyncio.sleep(0.002)
                yield chunk

        results = []
        async for tool_call, text in interceptor.process_stream(complex_async_chunks()):
            if tool_call:
                if "name" not in tool_call or "arguments" not in tool_call:
                    results.append(f"INVALID_TOOL: {tool_call}")
                else:
                    results.append(f"TOOL: {tool_call}")
            if text:
                results.append(
                    f"TEXT: {repr(text[:50])}{'...' if len(text) > 50 else ''}"
                )

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

        # Test 3: Async stream boundary cases
        print("\nTest 3 - Async stream boundary cases:")
        interceptor = ToolInterceptor()

        async def boundary_async_chunks():
            # Extreme splitting case
            chunks = list(
                '<tool_call>{"name": "boundary_test", "arguments": {}}</tool_call>'
            )
            for chunk in chunks:
                await asyncio.sleep(0.001)
                yield chunk

        results = []
        async for tool_call, text in interceptor.process_stream(
            boundary_async_chunks()
        ):
            if tool_call:
                if "name" not in tool_call or "arguments" not in tool_call:
                    results.append(f"INVALID_TOOL: {tool_call}")
                else:
                    results.append(f"TOOL: {tool_call['name']}")
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

        # Test 4: Async stream error handling
        print("\nTest 4 - Async stream error handling:")
        interceptor = ToolInterceptor()

        async def error_async_chunks():
            chunks = [
                "Normal text ",
                "<tool_call>",
                '{"name": "test", "arguments": bad json}',
                "</tool_call>",
                " Continue text",
            ]
            for chunk in chunks:
                await asyncio.sleep(0.001)
                yield chunk

        results = []
        async for tool_call, text in interceptor.process_stream(error_async_chunks()):
            if tool_call:
                results.append(f"TOOL: {tool_call}")
            if text:
                results.append(f"TEXT: {repr(text)}")

        print(f"Result count: {len(results)}")
        for result in results:
            print(f"  {result}")

    def test_mixed_scenarios():
        """Test mixed scenarios"""
        print("\n--- Mixed scenario tests ---")

        # Test type detection
        print("\nTest - Automatic type detection:")
        interceptor = ToolInterceptor()

        # Sync iterator
        sync_chunks = [
            "sync ",
            '<tool_call>{"name": "sync_test", "arguments": {}}</tool_call>',
        ]
        print("Sync iterator detection:")
        sync_results = list(interceptor.process_stream(iter(sync_chunks)))
        print(f"  Sync results: {len(sync_results)} items")

        # Test generator function
        def sync_generator():
            yield "generator "
            yield '<tool_call>{"name": "generator_test", "arguments": {}}</tool_call>'

        print("Sync generator detection:")
        gen_results = list(interceptor.process_stream(sync_generator()))
        print(f"  Generator results: {len(gen_results)} items")

    # Run sync tests
    test_sync_stream()

    # Run async tests
    asyncio.run(test_async_stream())

    # Run mixed scenario tests
    test_mixed_scenarios()


def test_tool_calls_to_openai():
    """Test tool_calls_to_openai function"""
    print("\n=== Testing tool_calls_to_openai function ===")

    tool_calls = [
        {"name": "calculate", "arguments": {"expression": "2 + 3"}},
        {"name": "get_weather", "arguments": {"location": "Beijing"}},
    ]

    # Test chat_completion format
    openai_format = tool_calls_to_openai(tool_calls, api_format="chat_completion")

    print(f"Conversion successful: {len(openai_format) == 2}")
    print(f"First call ID: {openai_format[0].id}")
    print(f"First call type: {openai_format[0].type}")
    print(f"First call function name: {openai_format[0].function.name}")
    print(f"First call arguments type: {type(openai_format[0].function.arguments)}")

    # Test response format
    response_format = tool_calls_to_openai(tool_calls, api_format="response")
    print(f"\nResponse format conversion successful: {len(response_format) == 2}")
    print(f"First response call name: {response_format[0].name}")
    print(f"First response call status: {response_format[0].status}")


def test_edge_cases():
    """Test edge cases and error conditions"""
    print("\n=== Testing edge cases ===")

    # Test empty tool calls
    interceptor = ToolInterceptor()

    # Test with None arguments
    response_with_none = '<tool_call>{"name": "test", "arguments": null}</tool_call>'
    tool_calls, remaining = interceptor.process(response_with_none)
    print(
        f"None arguments handled: {tool_calls[0]['arguments'] is None if tool_calls else False}"
    )

    # Test with missing arguments field
    response_missing_args = '<tool_call>{"name": "test"}</tool_call>'
    tool_calls, remaining = interceptor.process(response_missing_args)
    print(f"Missing arguments field: {tool_calls}")

    # Test with missing name field
    response_missing_name = '<tool_call>{"arguments": {"value": 1}}</tool_call>'
    tool_calls, remaining = interceptor.process(response_missing_name)
    print(f"Missing name field: {tool_calls}")

    # Test completely empty tool call
    response_empty = "<tool_call>{}</tool_call>"
    tool_calls, remaining = interceptor.process(response_empty)
    print(f"Empty tool call: {tool_calls}")


if __name__ == "__main__":
    test_handle_tools()
    test_tool_interceptor()
    test_tool_interceptor_stream()
    test_tool_calls_to_openai()
    test_edge_cases()
    print("\nAll tests completed!")
