"""
tool_prompt_template.py
-----------------------

A tiny helper for converting OpenAI–style *function-calling* fields
(`tools`, `tool_choice`, `parallel_tool_calls`) into a single system
prompt that can be sent to models without native function-calling
support.

Usage
=====
>>> python -m argoproxy.utils.tool_call_template
(or see the __main__ block below)
"""

import json
import re
import secrets
import string
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from ..types.function_call import ChatCompletionMessageToolCall, Function

Tools = List[Dict[str, Any]]
ToolChoice = Union[str, Dict[str, Any], None]


PROMPT_SKELETON = """You are an AI assistant that can optionally call pre-defined tools (“functions”).
Follow every rule below.

### 1. Available tools
```json
{tools_json}
```

### 2. Caller preference (tool_choice)
```json
{tool_choice_json}
```
• "none" → answer normally or pick a tool yourself.  
• "auto" → decide freely.  
• Object with "name" → call that tool if relevant.

### 3. Parallel calls flag
parallel_tool_calls = {parallel_flag}  
• true  → you MAY return multiple tool calls in one response.  
• false → return at most **one** tool call.

### 4. Response format  (⛔ DO NOT DEVIATE)
• If you are calling tool(s):
  1. Start your reply with the tag `<tool_call>` **as the very first token**.  
  2. Write ONLY valid JSON inside the tag, matching the schema below.  
  3. Close the tag with `</tool_call>`.  
  4. After **two newline characters** (`\\n\\n`) you MAY continue with normal
     natural-language content (no extra tags).

• If you are **not** calling any tool, simply reply in natural language—do **not** output any tags.

Single call (or parallel_tool_calls = false):
<tool_call>
{{
  "name": "<tool-name>",
  "arguments": {{ ... }}
}}
</tool_call>

Multiple calls (allowed only if parallel_tool_calls == true):
<tool_call>
{{
  "tool_calls": [
    {{ "name": "<tool-1>", "arguments": {{ ... }} }},
    {{ "name": "<tool-2>", "arguments": {{ ... }} }}
  ]
}}
</tool_call>

Always obey the JSON schemas exactly and never invent extra keys.
"""


def build_tool_prompt(
    tools: Tools,
    tool_choice: ToolChoice = None,
    *,
    parallel_tool_calls: bool = False,
    json_indent: int = 2,
) -> str:
    """
    Return a system-prompt string embedding `tools`, `tool_choice`
    and `parallel_tool_calls`.

    Parameters
    ----------
    tools : list[dict]
        The exact array you would pass to the OpenAI API.
    tool_choice : str | dict | None
        "none", "auto", or an object with "name", etc.
    parallel_tool_calls : bool
        Whether multiple tool calls may be returned in one turn.
    json_indent : int
        Pretty-print indentation for embedded JSON blobs.

    Returns
    -------
    str
        A fully formatted system prompt.
    """
    # Dump JSON with stable key order for readability
    tools_json = json.dumps(tools, indent=json_indent, ensure_ascii=False)
    tool_choice_json = json.dumps(
        tool_choice if tool_choice is not None else "none",
        indent=json_indent,
        ensure_ascii=False,
    )
    parallel_flag = "true" if parallel_tool_calls else "false"

    return PROMPT_SKELETON.format(
        tools_json=tools_json,
        tool_choice_json=tool_choice_json,
        parallel_flag=parallel_flag,
    )


def handle_tools(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process input data containing tool calls.

    This function will:
    1. Check if input data contains tool-related fields (tools, tool_choice, parallel_tool_calls)
    2. If present, generate tool call system prompt and add it to system messages
    3. Return processed data

    Parameters
    ----------
    data : dict
        Dictionary containing request data, may include:
        - tools: List of tool definitions
        - tool_choice: Tool selection preference
        - parallel_tool_calls: Whether to allow parallel tool calls
        - messages: Message list
        - system: System message

    Returns
    -------
    dict
        Processed data dictionary
    """
    # Check if there are tool-related fields
    tools = data.get("tools")
    if not tools:
        return data

    # Get tool call related parameters
    tool_choice = data.get("tool_choice")
    parallel_tool_calls = data.get("parallel_tool_calls", False)

    # Generate tool call prompt
    tool_prompt = build_tool_prompt(
        tools=tools, tool_choice=tool_choice, parallel_tool_calls=parallel_tool_calls
    )

    # Add tool prompt to system messages
    if "messages" in data:
        # Handle messages format
        messages = data["messages"]

        # Find existing system message
        system_msg_found = False
        for _, msg in enumerate(messages):
            if msg.get("role") == "system":
                # Add tool prompt to existing system message
                existing_content = msg.get("content", "")
                msg["content"] = f"{existing_content}\n\n{tool_prompt}".strip()
                system_msg_found = True
                break

        # If no system message found, add one at the beginning
        if not system_msg_found:
            system_message = {"role": "system", "content": tool_prompt}
            messages.insert(0, system_message)

    elif "system" in data:
        # Handle direct system field
        existing_system = data["system"]
        if isinstance(existing_system, str):
            data["system"] = f"{existing_system}\n\n{tool_prompt}".strip()
        elif isinstance(existing_system, list):
            data["system"] = existing_system + [tool_prompt]
    else:
        # If no system message, create one
        data["system"] = tool_prompt

    # Remove original tool-related fields as they've been converted to prompts
    data.pop("tools", None)
    data.pop("tool_choice", None)
    data.pop("parallel_tool_calls", None)

    return data


def generate_id(
    mode: Literal["chat_completion", "response"] = "chat_completion",
    chat_len: int = 22,
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
        suffix = "".join(secrets.choice(ALPHANUM) for _ in range(chat_len))
        return f"call_{suffix}"
    elif mode == "response":
        # 24 bytes → 48 hex chars (matches your example)
        return f"fc_{secrets.token_hex(24)}"
    else:
        raise ValueError(f"Unknown mode: {mode!r}")


# ---------------------------------------------------------------------------#
# Example usage
# ---------------------------------------------------------------------------#
if __name__ == "__main__":  # pragma: no cover
    # --- 1. Define tools exactly as you would for the OpenAI API ------------
    tools_example = [
        {
            "name": "get_weather",
            "description": "Get the current weather in a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
        {
            "name": "news_headlines",
            "description": "Fetch top news headlines.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["politics", "technology", "sports"],
                    },
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["category"],
            },
        },
    ]

    # --- 2. (Optional) choose preferred tool or "auto"/"none" --------------
    tool_choice_example = "auto"  # could also be {"name": "get_weather"} or "none"

    # --- 3. Build the prompt ------------------------------------------------
    prompt = build_tool_prompt(
        tools_example,
        tool_choice_example,
        parallel_tool_calls=True,
    )

    # --- 4. Send `prompt` as your *system* message when calling the model ---
    print(prompt)
