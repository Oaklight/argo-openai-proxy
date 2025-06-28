import json
from typing import List, Tuple, Optional, AsyncIterator
import asyncio


class ToolIterceptor:
    def __init__(self):
        self.buffer = ""
        self.in_tool_call = False
        self.tool_call_buffer = ""

    def process(self, text: str) -> Tuple[List[dict], str]:
        """Non-stream mode: Extract all tool_call JSONs and return remaining text."""
        tool_calls = []
        remaining_text = []

        # Reset state for non-stream processing
        self.buffer = text
        self.in_tool_call = False
        self.tool_call_buffer = ""

        while self.buffer:
            if not self.in_tool_call:
                start_idx = self.buffer.find("<tool_call>")
                if start_idx == -1:
                    # No more tool calls
                    remaining_text.append(self.buffer)
                    self.buffer = ""
                else:
                    # Found tool call start
                    if start_idx > 0:
                        remaining_text.append(self.buffer[:start_idx])
                    self.buffer = self.buffer[start_idx + len("<tool_call>") :]
                    self.in_tool_call = True
                    self.tool_call_buffer = ""
            else:
                end_idx = self.buffer.find("</tool_call>")
                if end_idx == -1:
                    # Should not happen in non-stream mode with complete text
                    self.tool_call_buffer += self.buffer
                    self.buffer = ""
                else:
                    # Found tool call end
                    self.tool_call_buffer += self.buffer[:end_idx]
                    try:
                        tool_call_json = json.loads(self.tool_call_buffer.strip())
                        tool_calls.append(tool_call_json)
                    except json.JSONDecodeError:
                        # Invalid JSON - add to remaining text as error marker
                        remaining_text.append(
                            f"<invalid>{self.tool_call_buffer}</invalid>"
                        )

                    self.buffer = self.buffer[end_idx + len("</tool_call>") :]
                    self.in_tool_call = False
                    self.tool_call_buffer = ""

        return tool_calls, "".join(remaining_text)

    def _could_be_partial_tag(self, text: str) -> bool:
        """Check if text could be the start of <tool_call> or </tool_call>"""
        for i in range(1, min(len(text) + 1, 11)):  # Max length of '</tool_call>'
            if "<tool_call>".startswith(text[-i:]) or "</tool_call>".startswith(
                text[-i:]
            ):
                return True
        return False

    async def process_async(
        self, chunk_iterator
    ) -> AsyncIterator[Tuple[Optional[dict], Optional[str]]]:
        """
        Stream mode: Process chunks and yield tool calls or text as they complete.

        Yields:
            (tool_call_dict, None) when a tool_call is fully parsed
            (None, text_chunk) for regular text between tool calls
        """
        self.buffer = ""
        self.in_tool_call = False
        self.tool_call_buffer = ""

        async for chunk in chunk_iterator:
            self.buffer += chunk

            while True:
                if not self.in_tool_call:
                    start_idx = self.buffer.find("<tool_call>")
                    if start_idx == -1:
                        # No complete tool call start found
                        if self._could_be_partial_tag(self.buffer):
                            # Might be partial tag at end, keep in buffer
                            break
                        else:
                            # Safe to emit all as text
                            if self.buffer:
                                yield None, self.buffer
                            self.buffer = ""
                            break
                    else:
                        # Emit text before tool call
                        if start_idx > 0:
                            yield None, self.buffer[:start_idx]
                        self.buffer = self.buffer[start_idx + len("<tool_call>") :]
                        self.in_tool_call = True
                        self.tool_call_buffer = ""
                else:
                    end_idx = self.buffer.find("</tool_call>")
                    if end_idx == -1:
                        # End tag not found yet
                        if self._could_be_partial_tag(self.buffer):
                            # Might have partial end tag, keep some in buffer
                            safe_length = max(
                                0, len(self.buffer) - 11
                            )  # Length of '</tool_call>'
                            if safe_length > 0:
                                self.tool_call_buffer += self.buffer[:safe_length]
                                self.buffer = self.buffer[safe_length:]
                        else:
                            # No partial tag possible, buffer all
                            self.tool_call_buffer += self.buffer
                            self.buffer = ""
                        break
                    else:
                        # Found end tag
                        self.tool_call_buffer += self.buffer[:end_idx]
                        try:
                            tool_call_json = json.loads(self.tool_call_buffer.strip())
                            yield tool_call_json, None
                        except json.JSONDecodeError:
                            # Invalid JSON
                            yield None, f"<invalid>{self.tool_call_buffer}</invalid>"

                        self.buffer = self.buffer[end_idx + len("</tool_call>") :]
                        self.in_tool_call = False
                        self.tool_call_buffer = ""

        # Handle any remaining content
        if self.in_tool_call:
            # Unclosed tool call
            if self.tool_call_buffer or self.buffer:
                yield None, f"<invalid>{self.tool_call_buffer}{self.buffer}</invalid>"
        elif self.buffer:
            yield None, self.buffer


# Assuming ToolIterceptor is imported or defined above


def get_test_cases():
    """Returns a list of (description, content) tuples for testing"""
    return [
        # Basic cases
        ("Empty response", ""),
        ("Only text, no tool calls", "This is just plain text with no tool calls."),
        (
            "Only tool call, no text",
            '<tool_call>{"name": "test", "args": {}}</tool_call>',
        ),
        # Edge cases with whitespace/newlines
        (
            "Tool call with lots of whitespace",
            '\n\n\n<tool_call>\n\n{\n  "name": "test",\n  "args": {}\n}\n\n</tool_call>\n\n\n',
        ),
        # Multiple tool calls
        (
            "Three consecutive tool calls",
            '<tool_call>{"name": "first", "id": 1}</tool_call><tool_call>{"name": "second", "id": 2}</tool_call><tool_call>{"name": "third", "id": 3}</tool_call>',
        ),
        (
            "Multiple tool calls with text between",
            'Starting text\n<tool_call>{"name": "add", "args": {"a": 1, "b": 2}}</tool_call>\nMiddle text\n<tool_call>{"name": "multiply", "args": {"a": 3, "b": 4}}</tool_call>\nEnding text',
        ),
        # Complex JSON structures
        (
            "Nested JSON in tool call",
            '<tool_call>{"name": "complex", "args": {"nested": {"deep": {"value": 42}}, "array": [1, 2, {"key": "value"}]}}</tool_call>',
        ),
        (
            "Tool call with escaped quotes",
            '<tool_call>{"name": "echo", "args": {"message": "He said \\"Hello\\" to me"}}</tool_call>',
        ),
        # Invalid cases
        (
            "Unclosed tool call tag",
            'Some text <tool_call>{"name": "test", "incomplete": true',
        ),
        (
            "Missing closing tag",
            'Text before <tool_call>{"name": "test"} and text after without closing',
        ),
        (
            "Invalid JSON in tool call",
            '<tool_call>{"name": "bad", invalid json here}</tool_call>',
        ),
        ("Empty tool call", "Text <tool_call></tool_call> more text"),
        (
            "Nested tool calls (invalid)",
            '<tool_call>{"name": "outer", "content": "<tool_call>nested</tool_call>"}</tool_call>',
        ),
        # Special characters and edge cases
        (
            "Tool call with special characters",
            '<tool_call>{"name": "special", "args": {"text": "Special chars: < > & \' \\" \\n \\t"}}</tool_call>',
        ),
        (
            "Multiple empty lines between content",
            'First paragraph\n\n\n\n<tool_call>{"name": "test"}</tool_call>\n\n\n\nSecond paragraph',
        ),
        # Real-world complex example
        (
            "Complex multi-step response",
            """I'll help you analyze this data. Let me start by loading the dataset.

<tool_call>{"name": "load_data", "args": {"file": "data.csv", "encoding": "utf-8"}}</tool_call>

Now let's check the basic statistics:

<tool_call>{"name": "describe", "args": {"columns": ["age", "income", "score"], "percentiles": [0.25, 0.5, 0.75]}}</tool_call>

Based on the statistics, I notice some outliers. Let me visualize this:

<tool_call>{"name": "plot", "args": {"type": "scatter", "x": "age", "y": "income", "color": "score", "title": "Age vs Income colored by Score"}}</tool_call>

The visualization confirms my hypothesis. Let's run a correlation analysis:

<tool_call>{"name": "correlate", "args": {"method": "pearson", "columns": ["age", "income", "score"]}}</tool_call>

In conclusion, there's a strong positive correlation between age and income (r=0.82).""",
        ),
        # Malformed tag variations
        ("Space in tag", 'Text < tool_call>{"name": "test"}</tool_call>'),
        ("Uppercase tags", 'Text <TOOL_CALL>{"name": "test"}</TOOL_CALL>'),
        ("Partial tag lookalikes", "Text with <tool and <tool_cal but not actual tags"),
        # Unicode and international characters
        (
            "Unicode in tool call",
            '<tool_call>{"name": "translate", "args": {"text": "Hello 世界 🌍 مرحبا"}}</tool_call>',
        ),
        # Very long content
        (
            "Very long tool call",
            f'<tool_call>{{"name": "long", "args": {{"data": "{("x" * 1000)}"}}}}</tool_call>',
        ),
    ]


def get_streaming_test_cases():
    """Returns streaming test cases as (description, chunks) tuples"""
    return [
        # Basic streaming
        (
            "Simple split in tag",
            ["Text before <tool_c", 'all>{"name": "test"}</tool_call> after'],
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
                '{"test": 1}',
                "</",
                "tool_call>",
            ],
        ),
        (
            "Split in JSON content",
            [
                '<tool_call>{"na',
                'me": "te',
                'st", "args"',
                ': {"value":',
                " 42}}</tool_call>",
            ],
        ),
        ("Split in closing tag", ['<tool_call>{"test": 1}</to', "ol_call> more text"]),
        # Multiple tool calls split
        (
            "Multiple tools split across chunks",
            [
                'First <tool_call>{"id": 1}',
                "</tool_call> middle ",
                '<tool_call>{"id":',
                " 2}</tool_c",
                "all> end",
            ],
        ),
        # Edge cases
        (
            "Empty chunks in stream",
            ["Text ", "", "<tool_call>", "", '{"test": 1}', "", "</tool_call>", ""],
        ),
        ("Very small chunks", list('Text <tool_call>{"name": "test"}</tool_call> end')),
        # Complex splits
        (
            "Split with partial tag lookalike",
            [
                "Text with <tool",
                ' but not tag, then <tool_call>{"real": true}</tool_call>',
            ],
        ),
        (
            "Newlines split across chunks",
            [
                "Line 1\n",
                "<tool_call>\n",
                '{\n  "test":',
                " true\n}\n</tool_call>",
                "\nLine 2",
            ],
        ),
        # Stress test
        (
            "Many small chunks with multiple tools",
            [
                "<",
                "tool_",
                'call>{"id":',
                " 1}</tool",
                "_call>text<to",
                'ol_call>{"',
                'id": 2}</',
                "tool_call>",
            ],
        ),
        # Invalid JSON split
        (
            "Invalid JSON across chunks",
            ['<tool_call>{"bad"', ": invalid json", "}</tool_call>"],
        ),
        # Unicode split
        (
            "Unicode split across chunks",
            ['<tool_call>{"text": "Hello ', '世界"}</tool_call>'],
        ),
    ]


async def run_all_tests():
    print("=" * 80)
    print("COMPREHENSIVE CONTENT SCREENER TESTS")
    print("=" * 80)

    # Non-streaming tests
    print("\n### NON-STREAMING TESTS ###\n")
    for desc, content in get_test_cases():
        print(f"Test: {desc}")
        print(f"Input: {repr(content[:100])}{'...' if len(content) > 100 else ''}")

        cs = ToolIterceptor()
        try:
            tool_calls, clean_text = cs.process(content)
            print(f"Tool calls: {tool_calls}")
            print(
                f"Clean text: {repr(clean_text[:100])}{'...' if len(clean_text) > 100 else ''}"
            )
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
        print("-" * 40)

    # Streaming tests
    print("\n### STREAMING TESTS ###\n")
    for desc, chunks in get_streaming_test_cases():
        print(f"Test: {desc}")
        print(f"Chunks: {chunks[:3]}{'...' if len(chunks) > 3 else ''}")

        async def chunk_generator():
            for chunk in chunks:
                await asyncio.sleep(0.001)
                yield chunk

        cs = ToolIterceptor()
        results = []
        try:
            async for tool_call, text in cs.process_async(chunk_generator()):
                if tool_call:
                    results.append(("TOOL", tool_call))
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

# if __name__ == "__main__":
#     # Test with your sample responses
#     samples = [
#         'I will use the `add` tool to calculate the sum of 15 and 27.\n\n<tool_call>\n{\n  "name": "add",\n  "arguments": {\n    "a": 15,\n    "b": 27\n  }\n}\n</tool_call>',
#         '<tool_call>\n{\n  "name": "add",\n  "arguments": {\n    "a": 15,\n    "b": 27\n  }\n}\n</tool_call>',
#         '<tool_call>\n{\n  "name": "add",\n  "arguments": {\n    "a":15,\n    "b": 27\n  }\n}\n</tool_call>\n\nStep-by-step reasoning:\n1. We take 15 and 27 as the two numbers.\n2. We add them together through the tool. \n3. This will produce the sum 42.',
#         # Multiple tool calls example
#         'Let me calculate both operations:\n<tool_call>{"name": "add", "arguments": {"a": 15, "b": 27}}</tool_call>\n<tool_call>{"name": "multiply", "arguments": {"a": 6, "b": 7}}</tool_call>\nThe results are above.',
#     ]

#     print("=== Non-stream mode tests ===")
#     for i, sample in enumerate(samples):
#         print(f"\nSample {i + 1}:")
#         cs = ToolIterceptor()
#         tool_calls, clean_text = cs.process(sample)
#         print(f"Tool calls: {tool_calls}")
#         print(f"Clean text: {repr(clean_text)}")

#     print("\n\n=== Stream mode test ===")
#     # Simulate streaming with chunks that split across boundaries
#     stream_chunks = [
#         "Let me calculate: <tool_ca",
#         'll>{"name": "add", "argum',
#         'ents": {"a": 15, "b": 27}}',
#         '</tool_call> and also <tool_call>{"name"',
#         ': "multiply", "arguments": {"a": 6, "b": 7}}</tool_call> Done!',
#     ]

#     async def dummy_chunk_iterator():
#         for chunk in stream_chunks:
#             await asyncio.sleep(0.01)
#             yield chunk

#     async def run_stream_test():
#         cs = ToolIterceptor()
#         results = []
#         async for tool_call, text in cs.process_async(dummy_chunk_iterator()):
#             if tool_call:
#                 results.append(f"Tool: {tool_call}")
#             if text:
#                 results.append(f"Text: {repr(text)}")

#         print("\nStream results:")
#         for r in results:
#             print(r)

#     asyncio.run(run_stream_test())
