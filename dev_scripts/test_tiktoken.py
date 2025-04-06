import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from argoproxy.utils import get_tiktoken_encoding_model

if __name__ == "__main__":
    from argoproxy.constants import CHAT_MODELS, EMBED_MODELS

    models = dict()
    models.update(EMBED_MODELS)
    models.update(CHAT_MODELS)

    for argoname, name in models.items():
        print("-" * 10, argoname, "-" * 10)
        print(get_tiktoken_encoding_model(argoname))
        print(get_tiktoken_encoding_model(name))
