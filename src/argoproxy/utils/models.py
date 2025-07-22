from typing import Any, Dict, Literal, Union

from pydantic import ValidationError

from ..types.function_call import ChatCompletionNamedToolChoiceParam


def determine_model_family(
    model: str = "gpt4o",
) -> Literal["openai", "anthropic", "google", "unknown"]:
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


def resemble_type(obj: object, cls: type) -> bool:
    """Check if the object's class matches the given class type.

    Args:
        obj (object): The object to check.
        cls (type): The class type to compare against.

    Returns:
        bool: True if the object's class name matches the given class type name, False otherwise.
    """
    class_name = obj.__class__.__name__

    if class_name == cls.__name__:
        return True
    return False

def validate_tool_choice(tool_choice: Union[str, Dict[str, Any]]) -> None:
    """Helper function to validate tool_choice parameter.

    Args:
        tool_choice: The tool choice parameter to validate.

    Raises:
        ValueError: If tool_choice is invalid.
    """
    if isinstance(tool_choice, str):
        valid_strings = ["none", "auto", "required"]
        if tool_choice not in valid_strings:
            raise ValueError(
                f"Invalid tool_choice string '{tool_choice}'. "
                f"Must be one of: {', '.join(valid_strings)}"
            )
    elif isinstance(tool_choice, dict):
        try:
            ChatCompletionNamedToolChoiceParam.model_validate(tool_choice, strict=False)
        except ValidationError as e:
            raise ValueError(f"Invalid tool_choice dict structure: {e}")
    else:
        raise ValueError(
            f"Invalid tool_choice type '{type(tool_choice).__name__}'. "
            f"Must be str or dict"
        )
