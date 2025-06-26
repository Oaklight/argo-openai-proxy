# Model definitions with primary names as keys and aliases as strings or lists
import fnmatch

_CHAT_MODELS = {
    # openai
    "gpt35": "argo:gpt-3.5-turbo",
    "gpt35large": "argo:gpt-3.5-turbo-16k",
    "gpt4": "argo:gpt-4",
    "gpt4large": "argo:gpt-4-32k",
    "gpt4turbo": "argo:gpt-4-turbo",
    "gpt4o": "argo:gpt-4o",
    "gpt4olatest": "argo:gpt-4o-latest",
    "gpto1mini": ["argo:gpt-o1-mini", "argo:o1-mini"],
    "gpto3mini": ["argo:gpt-o3-mini", "argo:o3-mini"],
    "gpto1": ["argo:gpt-o1", "argo:o1"],
    "gpto1preview": ["argo:gpt-o1-preview", "argo:o1-preview"],  # about to retire
    "gpto3": ["argo:gpt-o3", "argo:o3"],
    "gpto4mini": ["argo:gpt-o4-mini", "argo:o4-mini"],
    "gpt41": "argo:gpt-4.1",
    "gpt41mini": "argo:gpt-4.1-mini",
    "gpt41nano": "argo:gpt-4.1-nano",
    # gemini
    "gemini25pro": "argo:gemini-2.5-pro",
    "gemini25flash": "argo:gemini-2.5-flash",
    # claude
    "claudeopus4": ["argo:claude-opus-4", "argo:claude-4-opus"],
    "claudesonnet4": ["argo:claude-sonnet-4", "argo:claude-4-sonnet"],
    "claudesonnet37": ["argo:claude-sonnet-3.7", "argo:claude-3.7-sonnet"],
    "claudesonnet35v2": ["argo:claude-sonnet-3.5-v2", "argo:claude-3.5-sonnet-v2"],
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

# any models that unable to handle system prompt
NO_SYS_MSG_PATTERNS = {
    "argo:*o1-*",  # Matches any model name starting with 'argo:gpt-o1*' or 'argo:o1*'
    "gpto1preview",  # Explicitly matches gpto1preview
    "gpto1mini",  # Explicitly matches gpto1mini
    # Removed the broad "gpto1*" pattern
}

NO_SYS_MSG = [
    model
    for model in CHAT_MODELS
    if any(fnmatch.fnmatch(model, pattern) for pattern in NO_SYS_MSG_PATTERNS)
] + [
    short_name
    for short_name in _CHAT_MODELS.keys()
    if any(fnmatch.fnmatch(short_name, pattern) for pattern in NO_SYS_MSG_PATTERNS)
]

# any models that only able to handle single system prompt and no system prompt at all
OPTION_2_INPUT_PATTERNS = {
    "*gemini*",  # Matches any model name starting with 'gemini'
    "*claude*",  # Matches any model name starting with 'claude'
    "gpto3",
    "argo:*o3",  # Matches any model name starting with 'argo:gpt-o3' or 'argo:o3'
    "gpto4*",
    "argo:*o4*",
    "gpt41*",
    "argo:gpt-4.1*",  # Matches any model name starting with 'argo:gpt-4.1'
}

OPTION_2_INPUT = [
    model
    for model in CHAT_MODELS
    if any(fnmatch.fnmatch(model, pattern) for pattern in OPTION_2_INPUT_PATTERNS)
] + [
    short_name
    for short_name in _CHAT_MODELS.keys()
    if any(fnmatch.fnmatch(short_name, pattern) for pattern in OPTION_2_INPUT_PATTERNS)
]

NO_STREAM = OPTION_2_INPUT