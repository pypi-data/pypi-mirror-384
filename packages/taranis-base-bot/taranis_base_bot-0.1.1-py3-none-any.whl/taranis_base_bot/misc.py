import requests
from pydantic_settings import BaseSettings
from typing import Any, Callable
from importlib import import_module
from taranis_base_bot.protocols import Predictor


def create_request_parser(key: str, val_type: type) -> Callable[[dict], dict]:
    def request_parser(data: dict) -> dict[str, Any]:
        if key not in data:
            raise ValueError("Payload does not contain '{key}' key!")
        val = data[key]

        if val is None or not val:
            raise ValueError("No data provied for '{key}' key!")

        if not isinstance(val, val_type):
            raise ValueError("Data for '{key}' is not of type '{val_type}'")

        return {key: val}

    return request_parser


def get_model(config: BaseSettings) -> Predictor:
    try:
        module = import_module(f"{config.PACKAGE_NAME}.{config.MODEL}")
    except ModuleNotFoundError as e:
        raise ImportError(
            f"Package {config.PACKAGE_NAME} has no module named {config.MODEL}. Make sure the file {config.MODEL}.py exists"
        ) from e

    class_name = "".join(part.capitalize() for part in config.MODEL.split("_") if part)
    model_class = getattr(module, class_name, None)
    if model_class is None:
        raise ImportError(f"Module {config.MODEL} has no class named {class_name}. Make sure the class exists in {config.MODEL}.py")

    return model_class()


def get_hf_modelinfo(model_name: str) -> dict:
    """
    Fetch model metadata from Hugging Face.
    If anything fails, return a simple fallback.
    """
    try:
        url = f"https://huggingface.co/api/models/{model_name}"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"model": model_name, "error": str(e)}
