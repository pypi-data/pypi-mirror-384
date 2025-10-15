from flask import Flask
from typing import Callable, Any
from pydantic_settings import BaseSettings
from taranis_base_bot import blueprint
from taranis_base_bot.misc import get_model, get_hf_modelinfo, create_request_parser
from taranis_base_bot.decorators import api_key_required
from taranis_base_bot.blueprint import JSON
from taranis_base_bot.log import configure_logger


def create_default_bot_app(
    app_name: str,
    config: BaseSettings,
) -> Flask:
    model = get_model(config)

    predict_fn = model.predict

    def modelinfo_fn():
        if config.HF_MODEL_INFO:
            return get_hf_modelinfo(model.model_name)
        else:
            return model.modelinfo

    request_parser = create_request_parser(config.PAYLOAD_KEY, str)

    return create_app(app_name, config, "/", predict_fn, modelinfo_fn, request_parser, [api_key_required])


def create_app(
    name: str,
    config: BaseSettings,
    url_prefix: str,
    predict_fn: Callable[..., Any],
    modelinfo_fn: Callable[[], Any],
    request_parser: Callable[[JSON], dict[str, Any]],
    method_decorators: list[Callable],
) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)
    app.url_map.strict_slashes = False

    configure_logger(
        module=config.MODULE_ID,
        debug=config.DEBUG,
        colored=config.COLORED_LOGS,
        syslog_address=None,
    )

    bp = blueprint.create_service_blueprint(
        name=name,
        url_prefix=url_prefix,
        predict_fn=predict_fn,
        modelinfo_fn=modelinfo_fn,
        request_parser=request_parser,
        method_decorators=method_decorators,
    )
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    raise SystemExit("Cannot run taranis-base-bot directly. Use 'from taranis-base-bot import create_app' instead.")
