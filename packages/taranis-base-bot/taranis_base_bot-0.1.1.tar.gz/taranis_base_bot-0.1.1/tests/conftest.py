import pytest

from taranis_base_bot.config import get_common_settings
from taranis_base_bot.decorators import api_key_required
from taranis_base_bot.misc import get_hf_modelinfo

Config = get_common_settings()


@pytest.fixture
def client():
    from taranis_base_bot import create_app

    app = create_app(
        name="taranis_base_bot",
        config=Config,
        url_prefix="/",
        predict_fn=lambda **kwargs: kwargs,
        modelinfo_fn=lambda: {"model": "test"},
        request_parser=lambda x: x,
        method_decorators=[],
    )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_with_request_parser():
    from taranis_base_bot import create_app

    def request_parser(data: dict[str, str]) -> dict[str, str]:
        if "text" not in data:
            raise ValueError("Data must contain 'text' key")
        return {"text": data["text"]}

    app = create_app(
        name="taranis_base_bot",
        config=Config,
        url_prefix="/",
        predict_fn=lambda **kwargs: kwargs,
        modelinfo_fn=lambda: {"model": "test"},
        request_parser=request_parser,
        method_decorators=[],
    )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_with_predict():
    from taranis_base_bot import create_app

    def predict_func(text: str) -> dict[str, int]:
        if not isinstance(text, str):
            raise ValueError("Input is not a string!")
        return {"len": len(text)}

    app = create_app(
        name="taranis_base_bot",
        config=Config,
        url_prefix="/",
        predict_fn=predict_func,
        modelinfo_fn=lambda: {"model": "test"},
        request_parser=lambda x: x,
        method_decorators=[],
    )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_with_modelinfo_fn():
    from taranis_base_bot import create_app

    app = create_app(
        name="taranis_base_bot",
        config=Config,
        url_prefix="/",
        predict_fn=lambda **kwargs: kwargs,
        modelinfo_fn=lambda: get_hf_modelinfo("test_model"),
        request_parser=lambda x: x,
        method_decorators=[],
    )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def client_with_api_key(monkeypatch):
    """Client with API key authentication enabled"""
    # Temporarily set API key for testing
    monkeypatch.setenv("API_KEY", "test-api-key-123")

    # Reload config to pick up the new API key
    Config.API_KEY = "test-api-key-123"
    from taranis_base_bot import create_app

    app = create_app(
        name="taranis_base_bot_with_api_key",
        config=Config,
        url_prefix="/",
        predict_fn=lambda **kwargs: kwargs,
        modelinfo_fn=lambda: {"model": "test"},
        request_parser=lambda x: x,
        method_decorators=[api_key_required],
    )
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
