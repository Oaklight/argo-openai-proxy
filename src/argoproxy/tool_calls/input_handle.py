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
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import ValidationError

from ..types.function_call import (
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
)

Tools = List[Dict[str, Any]]
ToolChoice = Union[str, Dict[str, Any], None]

PROMPT_SKELETON = """You are an AI assistant that can optionally call pre-defined tools.
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

### 4. Response format  (CRITICAL RULES - DO NOT DEVIATE)

**DECISION POINT: Before writing ANY text, decide:**
- Am I calling a tool? → Start with `<tool_call>` IMMEDIATELY
- Am I not calling a tool? → Write natural language with NO tags

**IF CALLING TOOLS:**
1. Your response MUST start with `<tool_call>` as the **VERY FIRST characters** (no text before it!)
2. Write ONLY valid JSON inside the tag
3. Close with `</tool_call>`
4. After **two newlines** (`\\n\\n`) you MAY add natural language

**IF NOT CALLING TOOLS:**
- Write natural language ONLY
- DO NOT use any `<tool_call>` tags anywhere

**INVALID (will be rejected):**
- "Let me help you... <tool_call>"
- "I'll search for that. <tool_call>"
- Any text before <tool_call>

**VALID formats:**

- Single call (or parallel_tool_calls = false):
<tool_call> {{ "name": "<tool-name>", "arguments": {{ ... }} }} </tool_call>

Optional natural language here...

- Multiple calls (only if parallel_tool_calls == true):
<tool_call> {{ "name": "<tool-1>", "arguments": {{ ... }} }} </tool_call>
<tool_call> {{ "name": "<tool-2>", "arguments": {{ ... }} }} </tool_call>

Optional natural language here...

Remember: The FIRST character of your response determines everything. If it's not "<", you cannot use tools in that response.
"""


def build_tool_prompt(
    tools: Tools,
    tool_choice: ToolChoice = None,
    *,
    parallel_tool_calls: bool = False,
    json_indent: Optional[int] = None,
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
    json_indent : int | None
        Pretty-print indentation for embedded JSON blobs. Defaults to None for most compact output.

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


def model_family(model: str) -> Literal["openai", "anthropic", "google", "unknown"]:
    """
    Determine the model family based on the model name.
    """
    if "gpt" in model:
        return "openai"
    elif "claude" in model:
        return "anthropic"
    elif "gemini" in model:
        return "google"
    else:
        return "unknown"


def handle_tools_native(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Use native tool calls if the model supports it
    """
    # Check if there are tool-related fields
    tools = data.get("tools")
    if not tools:
        return data

    # Get tool call related parameters
    tool_choice = data.get("tool_choice")

    # Remove parallel_tool_calls from data for now
    parallel_tool_calls = data.pop("parallel_tool_calls", False)

    # use model to determine the data structure
    model_type = model_family(data.get("model", "gpt4o"))


def openai_tools_validator(
    tools: List[Dict[str, Any]],
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """
    Validate the tools for OpenAI models
    # TODO: response api needs special handling

    Args:
        tools: List of tools to validate, each tool is a json object
        tool_choice: Tool choice to validate, can be one of "none", "auto", or a json object
    """
    # pydantic type as validator
    tool_type = ChatCompletionToolParam

    # collect all validation errors
    errors = []
    for i, tool in enumerate(tools):
        try:
            tool_type.model_validate(tool)
        except ValidationError as e:
            errors.append(f"Tool {i}: {tool} - {e}")

    if tool_choice:
        tool_choice_type = ChatCompletionToolChoiceOptionParam
        # validate tool choice
        try:
            tool_choice_type.model_validate(tool_choice)
        except ValidationError as e:
            errors.append(f"Tool choice: {tool_choice} - {e}")

    # if any errors were found, raise with all of them
    if errors:
        raise ValueError("Invalid tool parameters found:\n" + "\n".join(errors))

    return tools


def openai_tools_to_anthropic_tools(
    tools: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Convert OpenAI tools to Anthropic tools
    """
    pass


def openai_tools_to_google_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert OpenAI tools to Google tools
    """
    pass


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

    print("=== Direct Tool Prompt Building ===")
    print(prompt)
    print("\n" + "=" * 50 + "\n")

    # --- 4. Demonstrate handle_tools function --------------------------------
    print("=== Demonstrate handle_tools Function ===")

    # Example input data (similar to OpenAI API request)
    input_data = {
        "messages": [
            {"role": "user", "content": "What's the weather like in Beijing today?"}
        ],
        "tools": tools_example,
        "tool_choice": tool_choice_example,
        "parallel_tool_calls": True,
    }

    print("Original input data:")
    print(json.dumps(input_data, indent=2, ensure_ascii=False))

    # Process tool calls
    processed_data = handle_tools(input_data.copy())

    print("\nProcessed data:")
    print(json.dumps(processed_data, indent=2, ensure_ascii=False))
