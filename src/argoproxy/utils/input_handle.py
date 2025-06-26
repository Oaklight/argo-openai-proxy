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
        if system_messages:
            data["system"] = "\n\n".join(system_messages).strip()

        prompt_messages = []
        for msg in data["messages"]:
            if msg["role"] in ("user", "assistant"):
                content = msg["content"]
                if isinstance(content, list):
                    # Extract text from content parts
                    texts = [
                        part["text"].strip()
                        for part in content
                        if part.get("type") == "text"
                    ]
                    # Join texts with double newline and add role prefix
                    prefixed_texts = f"{msg['role']}: " + "\n\n".join(texts).strip()
                    prompt_messages.append(prefixed_texts)
                else:
                    prompt_messages.append(f"{msg['role']}: {content}")

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


def handle_non_stream_only(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles non-streaming only models by setting stream to False.

    Args:
        data: The incoming request data.

    Returns:
        The modified request data with stream set to False.
    """
    data["stream"] = False
    return data
