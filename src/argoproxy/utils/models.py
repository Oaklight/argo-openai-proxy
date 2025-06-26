from typing import Dict, Literal, Optional

from ..models import ALL_MODELS


def resolve_model_name(
    model_name: str,
    default_model: Literal["argo:gpt-4o", "argo:text-embedding-3-small"],
    avail_models: Optional[Dict[str, str]] = None,
) -> str:
    """
    Resolves a model name to its primary model name using the flattened model mapping.

    Args:
        model_name: The input model name to resolve
        model_mapping: Dictionary mapping primary names to aliases (unused)
        default_model: Default model name to return if no match found

    Returns:
        The resolved primary model name or default_model if no match found
    """
    if not avail_models:
        avail_models = ALL_MODELS

    if model_name in avail_models.values():
        return model_name

    # Check if input exists in the flattened mapping
    if model_name in avail_models:
        return avail_models[model_name]

    return avail_models[default_model]
