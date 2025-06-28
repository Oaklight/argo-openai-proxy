"""
tool_prompt_template.py
-----------------------

A tiny helper for converting OpenAI–style *function-calling* fields
(`tools`, `tool_choice`, `parallel_tool_calls`) into a single system
prompt that can be sent to models without native function-calling
support.

Usage
=====
>>> python -m argoproxy.utils.tool_prompt_template
(or see the __main__ block below)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Union

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
{
  "name": "<tool-name>",
  "arguments": { ... }
}
</tool_call>

Multiple calls (allowed only if parallel_tool_calls == true):
<tool_call>
{
  "tool_calls": [
    { "name": "<tool-1>", "arguments": { ... } },
    { "name": "<tool-2>", "arguments": { ... } }
  ]
}
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
