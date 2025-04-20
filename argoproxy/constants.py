# Model definitions with primary names as keys and aliases as strings or lists
_CHAT_MODELS = {
    "gpt35": "argo:gpt-3.5-turbo",
    "gpt35large": "argo:gpt-3.5-turbo-16k",
    "gpt4": "argo:gpt-4",
    "gpt4large": "argo:gpt-4-32k",
    "gpt4turbo": "argo:gpt-4-turbo-preview",
    "gpt4o": "argo:gpt-4o",
    "gpt4olatest": "argo:gpt-4o-latest",
    "gpto1mini": ["argo:gpt-o1-mini", "argo:o1-mini"],
    "gpto3mini": ["argo:gpt-o3-mini", "argo:o3-mini"],
    "gpto1": ["argo:gpt-o1", "argo:o1"],
    "gpto1preview": ["argo:gpt-o1-preview", "argo:o1-preview"],
}

_EMBED_MODELS = {
    "ada002": "argo:text-embedding-ada-002",
    "v3small": "argo:text-embedding-3-small",
    "v3large": "argo:text-embedding-3-large",
}

# Create flattened mappings for lookup
def flatten_mapping(mapping):
    flat = {}
    for model, aliases in mapping.items():
        if isinstance(aliases, str):
            flat[aliases] = model
        else:
            for alias in aliases:
                flat[alias] = model
    return flat


CHAT_MODELS = flatten_mapping(_CHAT_MODELS)
EMBED_MODELS = flatten_mapping(_EMBED_MODELS)
ALL_MODELS = {**CHAT_MODELS, **EMBED_MODELS}

TIKTOKEN_ENCODING_PREFIX_MAPPING = {
    "gpto": "o200k_base",  # o-series
    "gpt4o": "o200k_base",  # gpt-4o
    # this order need to be preserved to correctly parse mapping
    "gpt4": "cl100k_base",  # gpt-4 series
    "gpt3": "cl100k_base",  # gpt-3 series
    "ada002": "cl100k_base",  # embedding
    "v3": "cl100k_base",  # embedding
}
