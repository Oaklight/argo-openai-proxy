import asyncio
import json
import secrets
import string
from typing import Any, AsyncIterator, Dict, List, Literal, Optional, Tuple, Union

from loguru import logger

from ..types.function_call import (
    ChatCompletionMessageToolCall,
    ChoiceDeltaToolCall,
    Function,
    ResponseFunctionToolCall,
)


class ToolIterceptor:
    def __init__(self):
        self.buffer = ""
        self.in_tool_call = False
        self.tool_call_buffer = ""

    def process(self, text: str) -> Tuple[Optional[List[dict]], str]:
        """Non-stream mode: Extract all tool_call JSONs and return remaining text."""
        tool_calls = []
        remaining_text = []

        logger.warning(f"Processing text: {text}")

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

        # Updated return statement to conditionally return None for tool_calls
        return (
            tool_calls if tool_calls else None,
            "".join(remaining_text),
        )

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


def convert_tool_calls_to_openai_format(
    tool_calls: List[Dict[str, Any]],
    *,
    is_stream: bool = False,
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
            if is_stream:
                pass
            else:
                tool_call_obj = ChatCompletionMessageToolCall(
                    id=generate_id(mode="chat_completion"),
                    function=Function(name=name, arguments=arguments),
                )
        else:
            if is_stream:
                pass
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
