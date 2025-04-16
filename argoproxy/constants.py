CHAT_MODELS = {
    "argo:gpt-3.5-turbo": "gpt35",
    "argo:gpt-3.5-turbo-16k": "gpt35large",
    "argo:gpt-4": "gpt4",
    "argo:gpt-4-32k": "gpt4large",
    "argo:gpt-4-turbo-preview": "gpt4turbo",
    "argo:gpt-4o": "gpt4o",
    "argo:gpt-4o-latest": "gpt4olatest",
    "argo:gpt-o1-mini": "gpto1mini",
    "argo:gpt-o3-mini": "gpto3mini",
    "argo:gpt-o1": "gpto1",
    "argo:gpt-o1-preview": "gpto1preview",
}

EMBED_MODELS = {
    "argo:text-embedding-ada-002": "ada002",
    "argo:text-embedding-3-small": "v3small",
    "argo:text-embedding-3-large": "v3large",
}

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
