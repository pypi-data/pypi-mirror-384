from functools import wraps
from flask import request, current_app
from taranis_base_bot.log import get_logger


def api_key_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        logger = get_logger()
        api_key = (current_app.config.get("API_KEY") or "").strip()
        if not api_key:
            return fn(*args, **kwargs)

        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            logger.warning("Missing Authorization Bearer")
            return {"error": "not authorized"}, 401
        if auth.removeprefix("Bearer ").strip() != api_key:
            logger.warning("Incorrect api key")
            return {"error": "not authorized"}, 401

        return fn(*args, **kwargs)

    return wrapper
