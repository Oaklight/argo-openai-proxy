from typing import Literal


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
