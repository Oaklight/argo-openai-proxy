import asyncio

from argoproxy.tool_calls.output_handle import ToolInterceptor


def get_test_cases():
    """Returns a list of (description, content) tuples for testing"""
    return [
        # Basic cases
        ("Empty response", ""),
        ("Only text, no tool calls", "This is just plain text with no tool calls."),
        (
            "Only tool call, no text",
            '<tool_call>{"name": "test", "arguments": {}}</tool_call>',
        ),
        # Edge cases with whitespace/newlines
        (
            "Tool call with lots of whitespace",
            '\n\n\n<tool_call>\n\n{\n  "name": "test",\n  "arguments": {}\n}\n\n</tool_call>\n\n\n',
        ),
        # Multiple tool calls
        (
            "Three consecutive tool calls",
            '<tool_call>{"name": "first", "arguments": {"id": 1}}</tool_call><tool_call>{"name": "second", "arguments": {"id": 2}}</tool_call><tool_call>{"name": "third", "arguments": {"id": 3}}</tool_call>',
        ),
        (
            "Multiple tool calls with text between",
            'Starting text\n<tool_call>{"name": "add", "arguments": {"a": 1, "b": 2}}</tool_call>\nMiddle text\n<tool_call>{"name": "multiply", "arguments": {"a": 3, "b": 4}}</tool_call>\nEnding text',
        ),
        # Complex JSON structures
        (
            "Nested JSON in tool call",
            '<tool_call>{"name": "complex", "arguments": {"nested": {"deep": {"value": 42}}, "array": [1, 2, {"key": "value"}]}}</tool_call>',
        ),
        (
            "Tool call with escaped quotes",
            '<tool_call>{"name": "echo", "arguments": {"message": "He said \\"Hello\\" to me"}}</tool_call>',
        ),
        # Invalid cases
        (
            "Unclosed tool call tag",
            'Some text <tool_call>{"name": "test", "arguments": {"incomplete": true}}',
        ),
        (
            "Missing closing tag",
            'Text before <tool_call>{"name": "test", "arguments": {}} and text after without closing',
        ),
        (
            "Invalid JSON in tool call",
            '<tool_call>{"name": "bad", invalid json here}</tool_call>',
        ),
        ("Empty tool call", "Text <tool_call></tool_call> more text"),
        (
            "Nested tool calls (invalid)",
            '<tool_call>{"name": "outer", "arguments": {"content": "<tool_call>nested</tool_call>"}}</tool_call>',
        ),
        # Special characters and edge cases
        (
            "Tool call with special characters",
            '<tool_call>{"name": "special", "arguments": {"text": "Special chars: < > & \' \\" \\n \\t"}}</tool_call>',
        ),
        (
            "Multiple empty lines between content",
            'First paragraph\n\n\n\n<tool_call>{"name": "test", "arguments": {}}</tool_call>\n\n\n\nSecond paragraph',
        ),
        # Real-world complex example
        (
            "Complex multi-step response",
            """I'll help you analyze this data. Let me start by loading the dataset.

<tool_call>{"name": "load_data", "arguments": {"file": "data.csv", "encoding": "utf-8"}}</tool_call>

Now let's check the basic statistics:

<tool_call>{"name": "describe", "arguments": {"columns": ["age", "income", "score"], "percentiles": [0.25, 0.5, 0.75]}}</tool_call>

Based on the statistics, I notice some outliers. Let me visualize this:

<tool_call>{"name": "plot", "arguments": {"type": "scatter", "x": "age", "y": "income", "color": "score", "title": "Age vs Income colored by Score"}}</tool_call>

The visualization confirms my hypothesis. Let's run a correlation analysis:

<tool_call>{"name": "correlate", "arguments": {"method": "pearson", "columns": ["age", "income", "score"]}}</tool_call>

In conclusion, there's a strong positive correlation between age and income (r=0.82).""",
        ),
        # Malformed tag variations
        (
            "Space in tag",
            'Text < tool_call>{"name": "test", "arguments": {}}</tool_call>',
        ),
        (
            "Uppercase tags",
            'Text <TOOL_CALL>{"name": "test", "arguments": {}}</TOOL_CALL>',
        ),
        ("Partial tag lookalikes", "Text with <tool and <tool_cal but not actual tags"),
        # Unicode and international characters
        (
            "Unicode in tool call",
            '<tool_call>{"name": "translate", "arguments": {"text": "Hello 世界 🌍 مرحبا"}}</tool_call>',
        ),
        # Very long content
        (
            "Very long tool call",
            f'<tool_call>{{"name": "long", "arguments": {{"data": "{("x" * 1000)}"}}}}</tool_call>',
        ),
    ]


def get_streaming_test_cases():
    """Returns streaming test cases as (description, chunks) tuples"""
    return [
        # Basic streaming
        (
            "Simple split in tag",
            [
                "Text before <tool_c",
                'all>{"name": "test", "arguments": {}}</tool_call> after',
            ],
        ),
        # Split in various positions
        (
            "Split in opening tag - 1 char at a time",
            [
                "<",
                "t",
                "o",
                "o",
                "l",
                "_",
                "c",
                "a",
                "l",
                "l",
                ">",
                '{"name": "test", "arguments": {"value": 1}}',
                "</",
                "tool_call>",
            ],
        ),
        (
            "Split in JSON content",
            [
                '<tool_call>{"na',
                'me": "te',
                'st", "arguments"',
                ': {"value":',
                " 42}}</tool_call>",
            ],
        ),
        (
            "Split in closing tag",
            [
                '<tool_call>{"name": "test", "arguments": {"value": 1}}</to',
                "ol_call> more text",
            ],
        ),
        # Multiple tool calls split
        (
            "Multiple tools split across chunks",
            [
                'First <tool_call>{"name": "first", "arguments": {"id": 1}}',
                "</tool_call> middle ",
                '<tool_call>{"name": "second", "arguments": {"id":',
                " 2}}</tool_c",
                "all> end",
            ],
        ),
        # Edge cases
        (
            "Empty chunks in stream",
            [
                "Text ",
                "",
                "<tool_call>",
                "",
                '{"name": "test", "arguments": {"value": 1}}',
                "",
                "</tool_call>",
                "",
            ],
        ),
        (
            "Very small chunks",
            list('Text <tool_call>{"name": "test", "arguments": {}}</tool_call> end'),
        ),
        # Complex splits
        (
            "Split with partial tag lookalike",
            [
                "Text with <tool",
                ' but not tag, then <tool_call>{"name": "real", "arguments": {"real": true}}</tool_call>',
            ],
        ),
        (
            "Newlines split across chunks",
            [
                "Line 1\n",
                "<tool_call>\n",
                '{\n  "name": "test",\n  "arguments":',
                ' {\n    "test": true\n  }\n}\n</tool_call>',
                "\nLine 2",
            ],
        ),
        # Stress test
        (
            "Many small chunks with multiple tools",
            [
                "<",
                "tool_",
                'call>{"name": ',
                '"first", "arguments":',
                ' {"id": 1}}</tool',
                "_call>",
                "<to",
                'ol_call>{"',
                'name": "second", "arguments": {"',
                'id": 2}}</',
                "tool_call>",
            ],
        ),
        # Invalid JSON split
        (
            "Invalid JSON across chunks",
            ['<tool_call>{"name": "bad"', ", invalid json", "}</tool_call>"],
        ),
        # Unicode split
        (
            "Unicode split across chunks",
            [
                '<tool_call>{"name": "unicode", "arguments": {"text": "Hello ',
                '世界"}}</tool_call>',
            ],
        ),
        # Test name/arguments field tracking
        (
            "Name field split across chunks",
            [
                '<tool_call>{"na',
                'me": "split_test"',
                ', "arguments": {"value": 42}}</tool_call>',
            ],
        ),
        (
            "Arguments field split across chunks",
            [
                '<tool_call>{"name": "test", "argum',
                'ents": {"a": 1, "b":',
                " 2}}</tool_call>",
            ],
        ),
    ]


async def run_all_tests():
    print("=" * 80)
    print("COMPREHENSIVE TOOL CALL INTERCEPTOR TESTS")
    print("=" * 80)

    # Non-streaming tests
    print("\n### NON-STREAMING TESTS ###\n")
    for desc, content in get_test_cases():
        print(f"Test: {desc}")
        print(f"Input: {repr(content[:100])}{'...' if len(content) > 100 else ''}")

        cs = ToolInterceptor()
        try:
            tool_calls, clean_text = cs.process(content)
            print(f"Tool calls: {tool_calls}")
            print(
                f"Clean text: {repr(clean_text[:100])}{'...' if len(clean_text) > 100 else ''}"
            )

            # Validate tool call structure
            if tool_calls:
                for i, tc in enumerate(tool_calls):
                    if not isinstance(tc, dict):
                        print(f"  WARNING: Tool call {i} is not a dict: {type(tc)}")
                    elif "name" not in tc or "arguments" not in tc:
                        print(f"  WARNING: Tool call {i} missing required fields: {tc}")

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
        print("-" * 40)

    # Streaming tests
    print("\n### ASYNC STREAMING TESTS ###\n")
    for desc, chunks in get_streaming_test_cases():
        print(f"Test: {desc}")
        print(f"Chunks: {chunks[:3]}{'...' if len(chunks) > 3 else ''}")

        async def chunk_generator():
            for chunk in chunks:
                await asyncio.sleep(0.001)
                yield chunk

        cs = ToolInterceptor()
        results = []
        try:
            async for tool_call, text in cs.process_stream(chunk_generator()):
                if tool_call:
                    # Validate tool call structure
                    if "name" not in tool_call or "arguments" not in tool_call:
                        results.append(("INVALID_TOOL", f"Missing fields: {tool_call}"))
                    else:
                        results.append(
                            (
                                "TOOL",
                                f"name={tool_call.get('name')}, args={tool_call.get('arguments')}",
                            )
                        )
                if text:
                    results.append(("TEXT", repr(text)))

            print(f"Results ({len(results)} items):")
            for rtype, content in results:
                print(f"  {rtype}: {content}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
        print("-" * 40)

    print("\n### SYNC STREAMING TESTS ###\n")
    for desc, chunks in get_streaming_test_cases():
        print(f"Test: {desc}")
        print(f"Chunks: {chunks[:3]}{'...' if len(chunks) > 3 else ''}")

        cs = ToolInterceptor()
        results = []
        try:
            for tool_call, text in cs.process_stream(iter(chunks)):
                if tool_call:
                    # Validate tool call structure
                    if "name" not in tool_call or "arguments" not in tool_call:
                        results.append(("INVALID_TOOL", f"Missing fields: {tool_call}"))
                    else:
                        results.append(
                            (
                                "TOOL",
                                f"name={tool_call.get('name')}, args={tool_call.get('arguments')}",
                            )
                        )
                if text:
                    results.append(("TEXT", repr(text)))

            print(f"Results ({len(results)} items):")
            for rtype, content in results:
                print(f"  {rtype}: {content}")
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
        print("-" * 40)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
