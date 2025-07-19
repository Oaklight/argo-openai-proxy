import json
import re
import secrets
import string
from typing import (
    Any,
    Dict,
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
    """
    Tool interceptor that handles both prompt-based and native tool calling responses.

    This class can process:
    1. Legacy prompt-based responses with <tool_call> tags
    2. Native tool calling responses from different model providers
    """

    def __init__(self):
        pass

    def process(
        self,
        response_content: Union[str, Dict[str, Any]],
        model_family: Literal["openai", "anthropic", "google"] = "openai",
    ) -> Tuple[Optional[List[dict]], str]:
        """
        Process response content and extract tool calls.

        Args:
            response_content: Either a string (legacy format) or dict (native format)
            model_family: Model family to determine the processing strategy

        Returns:
            Tuple of (list of tool calls or None, text content)
        """
        if isinstance(response_content, str):
            # Legacy prompt-based format
            return self._process_prompt_based(response_content)
        elif isinstance(response_content, dict):
            # Native tool calling format
            return self._process_native(response_content, model_family)
        else:
            logger.warning(
                f"Unexpected response content type: {type(response_content)}"
            )
            return None, str(response_content)

    def _process_prompt_based(self, text: str) -> Tuple[Optional[List[dict]], str]:
        """
        Process prompt-based responses with <tool_call> tags.

        Args:
            text: Text content containing potential <tool_call> tags

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

    def _process_native(
        self,
        response_data: Dict[str, Any],
        model_family: Literal["openai", "anthropic", "google"] = "openai",
    ) -> Tuple[Optional[List[Dict[str, Any]]], str]:
        """
        Process native tool calling responses from different model providers.

        Args:
            response_data: Response data containing content and tool_calls
            model: Model name to determine the processing strategy

        Returns:
            Tuple of (list of tool calls or None, text content)
        """

        if model_family == "openai":
            return self._process_openai_native(response_data)
        elif model_family == "anthropic":
            return self._process_anthropic_native(response_data)
        elif model_family == "google":
            return self._process_google_native(response_data)
        else:
            logger.warning(
                f"Unknown model family for model: {model_family}, falling back to OpenAI format"
            )
            return self._process_openai_native(response_data)

    def _process_openai_native(
        self, response_data: Dict[str, Any]
    ) -> Tuple[Optional[List[Dict[str, Any]]], str]:
        """
        Process OpenAI native tool calling response format.

        Expected format:
        {
            "content": "text response",
            "tool_calls": [
                {"name": "function_name", "arguments": {...}}
            ]
        }

        Args:
            response_data: OpenAI format response data

        Returns:
            Tuple of (list of tool calls or None, text content)
        """
        content = response_data.get("content", "")
        tool_calls = response_data.get("tool_calls", [])

        return tool_calls, content

    def _process_anthropic_native(
        self, response_data: Dict[str, Any]
    ) -> Tuple[Optional[List[dict]], str]:
        """
        Process Anthropic native tool calling response format.

        TODO: Implement Anthropic-specific tool calling format processing.

        Args:
            response_data: Anthropic format response data

        Returns:
            Tuple of (list of tool calls or None, text content)
        """
        # Placeholder implementation - to be implemented later
        logger.warning(
            "Anthropic native tool calling not implemented yet, falling back to OpenAI format"
        )
        raise NotImplementedError

    def _process_google_native(
        self, response_data: Dict[str, Any]
    ) -> Tuple[Optional[List[dict]], str]:
        """
        Process Google native tool calling response format.

        TODO: Implement Google-specific tool calling format processing.

        Args:
            response_data: Google format response data

        Returns:
            Tuple of (list of tool calls or None, text content)
        """
        # Placeholder implementation - to be implemented later
        logger.warning(
            "Google native tool calling not implemented yet, falling back to OpenAI format"
        )
        raise NotImplementedError


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
