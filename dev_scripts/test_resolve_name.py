import os

from argoproxy.models import CHAT_MODELS
from argoproxy.utils import resolve_model_name

MODEL = os.getenv("MODEL", "argo:gpt-4o")
DEFAULT_MODEL = "argo:gpt-4o"

resolved_name = resolve_model_name(MODEL, DEFAULT_MODEL, avail_models=CHAT_MODELS)
print(resolved_name)
