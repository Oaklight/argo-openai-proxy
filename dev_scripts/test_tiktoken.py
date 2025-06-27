from argoproxy.utils.tokens import get_tiktoken_encoding_model

if __name__ == "__main__":
    from argoproxy.models import ModelRegistry

    registry = ModelRegistry()

    for model_name, model_id in registry.available_models.items():
        print("-" * 10, model_name, "-" * 10)
        print(get_tiktoken_encoding_model(model_name))
        print(get_tiktoken_encoding_model(model_id))
