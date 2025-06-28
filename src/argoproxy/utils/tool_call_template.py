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


PROMPT_SKELETON = """You are an AI assistant that can optionally call pre-defined tools (a.k.a. “functions”).
Follow the rules exactly.

# 1. Tools you can call
The following JSON array defines every tool you may invoke.
Each element contains a `name`, a short `description`, and a JSON-Schema object `parameters` describing its arguments.
```json
{tools_json}
```

# 2. Preferred tool (optional)
The caller’s preference is:
```json
{tool_choice_json}
```
If "none", choose the best tool yourself (or none).
If an object with a "name", that tool SHOULD be called if relevant.
If "auto", decide freely.

# 3. Parallel tool calls
parallel_tool_calls = {parallel_flag}

• If true → you MAY call several tools *in the same turn*.
• If false → call at most one tool per turn.

# 4. How to respond when calling tools
If you decide to call tool(s), respond with **ONLY** one of the JSON snippets below—no extra text.

Single call (or parallel_tool_calls = false):
```json
{{
  "name": "<tool-name>",
  "arguments": {{ /* arguments object matching the schema */ }}
}}
```

Multiple calls (allowed only if parallel_tool_calls = true):
```json
{{
  "tool_calls": [
    {{
      "name": "<tool-1>",
      "arguments": {{ /* … */ }}
    }},
    {{
      "name": "<tool-2>",
      "arguments": {{ /* … */ }}
    }}
  ]
}}
```

# 5. Normal answer
If no tool is needed, reply normally in natural language.

Always respect the JSON schemas and never invent extra keys.
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
