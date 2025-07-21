from typing import Any, Dict, List


def deduplicate_and_concatenate(messages: List[str]) -> str:
    """
    Removes duplicates and concatenates messages with double newline separation.

    Args:
        messages (List[str]): List of message strings.

    Returns:
        str: Deduplicated, concatenated string.
    """
    return "\n\n".join(dict.fromkeys(messages)).strip()


def handle_multiple_entries_prompt(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deduplicates and merges 'system' and 'prompt' lists into single strings.

    Args:
        data (Dict[str, Any]): Dictionary with 'system' and 'prompt' keys.

    Returns:
        Dict[str, Any]: Updated dictionary with merged entries.
    """

    if "system" in data:
        if isinstance(data["system"], list):
            data["system"] = deduplicate_and_concatenate(data["system"])

    if "prompt" in data:
        if isinstance(data["prompt"], list):
            data["prompt"] = [deduplicate_and_concatenate(data["prompt"])]

    return data


def handle_option_2_input(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Segregates messages into 'system' and 'prompt' based on roles.

    Args:
        data (Dict[str, Any]): Dictionary with 'messages' list.

    Returns:
        Dict[str, Any]: Data split into 'system' and 'prompt'.
    """
    if "messages" in data:
        system_messages = [
            msg["content"]
            for msg in data["messages"]
            if msg["role"] in ("system", "developer")
        ]
        data["system"] = system_messages

        prompt_messages = []
        for msg in data["messages"]:
            if msg["role"] in ("user", "assistant"):
                content = msg["content"]
                if isinstance(content, list):
                    texts = [
                        part["text"].strip()
                        for part in content
                        if part.get("type") == "text"
                    ]
                    prefixed_texts = [
                        f"{msg['role']}: {text.strip()}" for text in texts
                    ]
                    prompt_messages.extend(prefixed_texts)
                else:
                    prompt_messages.append(f"{msg['role']}: {content.strip()}")

        data["prompt"] = prompt_messages
        del data["messages"]

    return data


def normalize_system_message_content(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes content field for system/developer role messages.
    
    Converts List[Dict] content to a single string for system/developer roles.
    
    Args:
        data: The request data containing messages.
        
    Returns:
        The modified request data with normalized content.
        
    Example:
        Input message:
        {
            "role": "system",
            "content": [{"type": "text", "text": "You are a helpful assistant"}]
        }
        
        Output message:
        {
            "role": "system",
            "content": "You are a helpful assistant"
        }
    """
    if "messages" in data and isinstance(data["messages"], list):
        for message in data["messages"]:
            if (
                message.get("role") in ("system", "developer")
                and "content" in message
                and isinstance(message["content"], list)
            ):
                # Extract text from list of content parts
                text_parts = []
                for part in message["content"]:
                    if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                        text_parts.append(str(part["text"]))
                
                # Join all text parts into a single string
                if text_parts:
                    message["content"] = "\n\n".join(text_parts).strip()
                else:
                    # Fallback: convert the entire list to string if no text parts found
                    message["content"] = str(message["content"])
    
    return data


def handle_no_sys_msg(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Changes 'system' messages to 'user' and merges into 'prompt'.

    Args:
        data (Dict[str, Any]): Dictionary with 'messages' list.

    Returns:
        Dict[str, Any]: Updated dictionary without 'system'.
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


def scrutinize_message_entries(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Scrutinizes entries in messages, ensuring each entry's text is a string.
    Uses str() to force casting for non-string text values.

    Args:
        data (Dict[str, Any]): Dictionary containing message data.

    Returns:
        Dict[str, Any]: Updated dictionary with string-casted text entries.
    """
    if "messages" in data and isinstance(data["messages"], list):
        for message in data["messages"]:
            if "content" in message:
                content = message["content"]
                
                # Handle list-type content (multipart messages)
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            part["text"] = str(part["text"])
                
                # Handle string-type content
                else:
                    message["content"] = str(content)
    
    # Handle system messages if they exist as separate entries
    if "system" in data:
        if isinstance(data["system"], list):
            data["system"] = [str(msg) for msg in data["system"]]
        else:
            data["system"] = str(data["system"])
    
    # Handle prompt messages if they exist as separate entries
    if "prompt" in data:
        if isinstance(data["prompt"], list):
            data["prompt"] = [str(msg) for msg in data["prompt"]]
        else:
            data["prompt"] = str(data["prompt"])
    
    return data
