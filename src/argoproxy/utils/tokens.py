import asyncio
from typing import List, Union

import tiktoken

from ..models import TIKTOKEN_ENCODING_PREFIX_MAPPING


def get_tiktoken_encoding_model(model: str) -> str:
    """
    Get tiktoken encoding name for a given model.
    If the model starts with 'argo:', use TIKTOKEN_ENCODING_PREFIX_MAPPING to find encoding.
    Otherwise use MODEL_TO_ENCODING mapping.
    """
    for prefix, encoding in TIKTOKEN_ENCODING_PREFIX_MAPPING.items():
        if model == prefix:
            return encoding
        if model.startswith(prefix):
            return encoding
    return "cl100k_base"


def extract_text_content(content: Union[str, list]) -> str:
    """Extract text content from message content which can be string or list of objects"""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                texts.append(item["text"])
            elif isinstance(item, str):
                texts.append(item)
        return " ".join(texts)
    return ""


def count_tokens(text: Union[str, List[str]], model: str) -> int:
    """
    Calculate token count for a given text using tiktoken.
    If the model starts with 'argo:', the part after 'argo:' is used
    to determine the encoding via a MODEL_TO_ENCODING mapping.
    """

    encoding_name = get_tiktoken_encoding_model(model)
    encoding = tiktoken.get_encoding(encoding_name)

    if isinstance(text, list):
        return sum([len(encoding.encode(each)) for each in text])

    return len(encoding.encode(text))


async def count_tokens_async(text: Union[str, List[str]], model: str) -> int:
    """
    Asynchronously calculate token count for a given text using tiktoken.
    Runs the token counting in a thread pool to avoid blocking the event loop.
    """
    return await asyncio.to_thread(count_tokens, text, model)


def calculate_prompt_tokens(data: dict, model: str) -> int:
    """
    Calculate prompt tokens from either messages or prompt field in the request data.
    Supports both string content and list of content objects in messages.

    Args:
        data: The request data dictionary
        model: The model name for token counting

    Returns:
        int: Total token count for the prompt/messages
    """

    if "messages" in data:
        messages_content = [
            extract_text_content(msg["content"])
            for msg in data["messages"]
            if "content" in msg
        ]
        prompt_tokens = count_tokens(messages_content, model)
        return prompt_tokens
    return count_tokens(data.get("prompt", ""), model)


async def calculate_prompt_tokens_async(data: dict, model: str) -> int:
    """
    Asynchronously calculate prompt tokens from either messages or prompt field in the request data.
    Runs the token calculation in a thread pool to avoid blocking the event loop.
    """
    return await asyncio.to_thread(calculate_prompt_tokens, data, model)
