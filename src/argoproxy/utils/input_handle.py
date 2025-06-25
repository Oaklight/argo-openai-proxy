from typing import Any, Dict


def handle_option_2_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transforms data for models requiring `system` and `prompt` structure only.

    Args:
        data: The incoming request data.

    Returns:
        The modified request data with `system` and `prompt`.
    """
    if "messages" in data:
        system_messages = [
            msg["content"] for msg in data["messages"] if msg["role"] == "system"
        ]
        data["system"] = system_messages[0] if system_messages else ""

        prompt_messages = [
            msg["content"]
            for msg in data["messages"]
            if msg["role"] in ("user", "assistant")
        ]
        data["prompt"] = prompt_messages
        del data["messages"]

    return data


def handle_no_sys_msg(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Converts `system` messages to `user` messages for models in NO_SYS_MSG.

    Args:
        data: The incoming request data.

    Returns:
        The modified request data without `system` messages.
    """
    if "messages" in data:
        for message in data["messages"]:
            if message["role"] == "system":
                message["role"] = "user"
    if "system" in data:
        data["prompt"] = (
            [data["system"]] + data["prompt"]
            if isinstance(data["system"], str)
            else data["system"] + data["prompt"]
        )
        del data["system"]

    return data
