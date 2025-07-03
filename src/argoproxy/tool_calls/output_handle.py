import inspect
import json
import re
import secrets
import string
from typing import (
    Any,
    AsyncIterator,
    Dict,
    Iterator,
    List,
    Literal,
    Optional,
    Tuple,
    Union,
    overload,
)

from loguru import logger

from ..types.function_call import (
    ChatCompletionMessageToolCall,
    ChoiceDeltaToolCall,
    Function,
    ResponseFunctionToolCall,
)


class ToolInterceptor:
    def __init__(self):
        self.buffer = ""
        self.in_tool_call = False
        self.tool_call_buffer = ""

    def process(self, text: str) -> Tuple[Optional[List[dict]], str]:
        """Non-stream mode: Extract all tool_call JSONs and preserve all non-tool-call text.

        Returns:
            Tuple of (list of tool calls or None, concatenated text from outside tool calls)
        """
        tool_calls = []
        text_parts = []
        last_end = 0

        for match in re.finditer(r"<tool_call>(.*?)</tool_call>", text, re.DOTALL):
            # Add text before this tool call
            if match.start() > last_end:
                text_parts.append(text[last_end : match.start()])

            # Process the tool call
            try:
                tool_calls.append(json.loads(match.group(1).strip()))
            except json.JSONDecodeError:
                # On JSON error, include the raw content as text
                text_parts.append(f"<invalid>{match.group(1)}</invalid>")

            last_end = match.end()

        # Add any remaining text after last tool call
        if last_end < len(text):
            text_parts.append(text[last_end:])

        return (
            tool_calls if tool_calls else None,
            "".join(
                text_parts
            ).lstrip(),  # Combine all text parts and strip leading whitespace
        )

    def _process_chunk_logic(
        self, chunk: str
    ) -> List[Tuple[Optional[dict], Optional[str]]]:
        """Core logic for processing a single chunk, returns list of (tool_call, text) tuples"""
        results = []
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
                            results.append((None, self.buffer))
                        self.buffer = ""
                        break
                else:
                    # Emit text before tool call
                    if start_idx > 0:
                        results.append((None, self.buffer[:start_idx]))
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
                        results.append((tool_call_json, None))
                    except json.JSONDecodeError:
                        # Invalid JSON
                        results.append(
                            (None, f"<invalid>{self.tool_call_buffer}</invalid>")
                        )

                    self.buffer = self.buffer[end_idx + len("</tool_call>") :]
                    self.in_tool_call = False
                    self.tool_call_buffer = ""

        return results

    def _finalize_processing(self) -> List[Tuple[Optional[dict], Optional[str]]]:
        """Handle any remaining content after all chunks are processed"""
        results = []
        if self.in_tool_call:
            # Unclosed tool call
            if self.tool_call_buffer or self.buffer:
                results.append(
                    (None, f"<invalid>{self.tool_call_buffer}{self.buffer}</invalid>")
                )
        elif self.buffer:
            results.append((None, self.buffer))
        return results

    @overload
    def process_stream(
        self, chunk_iterator: Iterator[str]
    ) -> Iterator[Tuple[Optional[dict], Optional[str]]]: ...

    @overload
    def process_stream(
        self, chunk_iterator: AsyncIterator[str]
    ) -> AsyncIterator[Tuple[Optional[dict], Optional[str]]]: ...

    def process_stream(
        self, chunk_iterator: Union[Iterator[str], AsyncIterator[str]]
    ) -> Union[
        Iterator[Tuple[Optional[dict], Optional[str]]],
        AsyncIterator[Tuple[Optional[dict], Optional[str]]],
    ]:
        """
        Process chunks and yield tool calls or text as they complete.

        The return type matches the input iterator type:
        - If chunk_iterator is sync Iterator, returns sync Iterator
        - If chunk_iterator is async AsyncIterator, returns AsyncIterator

        Yields:
            (tool_call_dict, None) when a tool_call is fully parsed
            (None, text_chunk) for regular text between tool calls
        """
        # Reset state
        self.buffer = ""
        self.in_tool_call = False
        self.tool_call_buffer = ""

        # Check if the iterator is async
        if hasattr(chunk_iterator, "__aiter__") or inspect.isasyncgen(chunk_iterator):
            return self._process_async_iterator(chunk_iterator)
        else:
            return self._process_sync_iterator(chunk_iterator)

    def _process_sync_iterator(
        self, chunk_iterator: Iterator[str]
    ) -> Iterator[Tuple[Optional[dict], Optional[str]]]:
        """Process synchronous iterator"""
        for chunk in chunk_iterator:
            results = self._process_chunk_logic(chunk)
            for result in results:
                yield result

        # Handle any remaining content
        final_results = self._finalize_processing()
        for result in final_results:
            yield result

    async def _process_async_iterator(
        self, chunk_iterator: AsyncIterator[str]
    ) -> AsyncIterator[Tuple[Optional[dict], Optional[str]]]:
        """Process asynchronous iterator"""
        async for chunk in chunk_iterator:
            results = self._process_chunk_logic(chunk)
            for result in results:
                yield result

        # Handle any remaining content
        final_results = self._finalize_processing()
        for result in final_results:
            yield result


def generate_id(
    *,
    mode: Literal["chat_completion", "response"] = "chat_completion",
) -> str:
    """
    Return a random identifier.

    Parameters
    ----------
    mode : {'chat_completion', 'response'}
        'chat_completion' →  call_<22-char base62 string>   (default)
        'response'        →  fc_<48-char hex string>
    chat_len : int
        Length of the suffix for the chat-completion variant.

    Examples
    --------
    >>> generate_id()
    'call_b9krJaIcuBM4lej3IyI5heVc'

    >>> generate_id(mode='response')
    'fc_68600a8868248199a436492a47a75e440766032408f75a09'
    """
    ALPHANUM = string.ascii_letters + string.digits
    if mode == "chat_completion":
        suffix = "".join(secrets.choice(ALPHANUM) for _ in range(22))
        return f"call_{suffix}"
    elif mode == "response":
        # 24 bytes → 48 hex chars (matches your example)
        return f"fc_{secrets.token_hex(24)}"
    else:
        raise ValueError(f"Unknown mode: {mode!r}")


@overload
def tool_calls_to_openai(
    tool_calls: List[Dict[str, Any]],
    *,
    api_format: Literal["chat_completion"] = "chat_completion",
) -> List[ChatCompletionMessageToolCall]: ...


@overload
def tool_calls_to_openai(
    tool_calls: List[Dict[str, Any]],
    *,
    api_format: Literal["response"],
) -> List[ResponseFunctionToolCall]: ...


def tool_calls_to_openai(
    tool_calls: List[Dict[str, Any]],
    *,
    api_format: Literal["chat_completion", "response"] = "chat_completion",
) -> List[Union[ChatCompletionMessageToolCall, ResponseFunctionToolCall]]:
    """Converts parsed tool calls to OpenAI API format.

    Args:
        tool_calls: List of parsed tool calls.
        is_stream: Whether the output is for streaming. Defaults to False.
        api_format: Output format type, either "chat_completion" or "response".
            Defaults to "chat_completion".

    Returns:
        List of tool calls in OpenAI function call object type. The specific type
        depends on the api_format parameter:
        - ChatCompletionMessageToolCall for "chat_completion"
        - ResponseFunctionToolCall for "response"
    """
    openai_tool_calls = []

    for call in tool_calls:
        arguments = json.dumps(call.get("arguments", ""))
        name = call.get("name", "")
        if api_format == "chat_completion":
            tool_call_obj = ChatCompletionMessageToolCall(
                id=generate_id(mode="chat_completion"),
                function=Function(name=name, arguments=arguments),
            )
        else:
            tool_call_obj = ResponseFunctionToolCall(
                arguments=arguments,
                call_id=generate_id(mode="chat_completion"),
                name=name,
                id=generate_id(mode="response"),
                status="completed",
            )
        openai_tool_calls.append(tool_call_obj)

    return openai_tool_calls


def tool_calls_to_openai_stream(
    tool_call: Dict[str, Any],
    *,
    tc_index: int = 0,
    api_format: Literal["chat_completion", "response"] = "chat_completion",
) -> ChoiceDeltaToolCall:
    """
    Converts a tool call dict to OpenAI-compatible tool call objects for streaming.

    Args:
        tool_calls: single tool call dict to convert.
        tc_index: The index of the tool call.
        api_format: The format to convert the tool calls to. Can be "chat_completion" or "response".

    Returns:
        An OpenAI-compatible stream tool call object.
    """

    arguments = json.dumps(tool_call.get("arguments", ""))
    name = tool_call.get("name", "")
    if api_format == "chat_completion":
        tool_call_obj = ChoiceDeltaToolCall(
            id=generate_id(mode="chat_completion"),
            function=Function(name=name, arguments=arguments),
            index=tc_index,
        )
    else:
        # tool_call_obj = ResponseFunctionToolCall(
        #     arguments=arguments,
        #     call_id=generate_id(mode="chat_completion"),
        #     name=name,
        #     id=generate_id(mode="response"),
        #     status="completed",
        # )
        raise NotImplementedError("response format is not implemented yet.")

    return tool_call_obj
