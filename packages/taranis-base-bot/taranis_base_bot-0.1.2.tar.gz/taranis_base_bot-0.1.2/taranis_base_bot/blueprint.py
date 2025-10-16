from typing import Callable, Any, Dict, List
from flask import Blueprint, jsonify, request
from flask.views import MethodView

JSON = Dict[str, Any]


class InferenceView(MethodView):
    """
    Generic POST endpoint that:
    - parses request JSON via `request_parser`
    - calls `predict_fn(**kwargs)`
    - returns JSON
    """

    def __init__(
        self,
        predict_fn: Callable[..., Any],
        request_parser: Callable[[Any], Dict[str, Any]],
    ) -> None:
        super().__init__()
        self._predict_fn = predict_fn
        self._parse = request_parser

    def post(self):
        data = request.get_json()
        if not isinstance(data, dict):
            return jsonify({"error": "Payload must be a dict!"}), 400
        try:
            kwargs = self._parse(data)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400

        try:
            result = self._predict_fn(**kwargs)
            return jsonify(result)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400


class HealthView(MethodView):
    def get(self):
        return jsonify({"status": "ok"})


class ModelInfoView(MethodView):
    def __init__(self, modelinfo_fn: Callable[[], Any]) -> None:
        super().__init__()
        self._modelinfo = modelinfo_fn

    def get(self):
        return jsonify(self._modelinfo())


def create_service_blueprint(
    *,
    name: str,
    url_prefix: str = "/",
    predict_fn: Callable[..., Any],
    modelinfo_fn: Callable[[], Any],
    request_parser: Callable[[JSON], Dict[str, Any]],
    method_decorators: List[Callable] | None = None,
):
    """
    Returns a Blueprint with three routes:
      POST   "/"         -> InferenceView
      GET    "/health"   -> HealthView
      GET    "/modelinfo"-> ModelInfoView

    - `method_decorators` are applied to the POST method
    """
    bp = Blueprint(name, __name__, url_prefix=url_prefix)

    inference_view = InferenceView.as_view(
        f"{name}_predict",
        predict_fn=predict_fn,
        request_parser=request_parser,
    )

    if method_decorators:
        for dec in reversed(method_decorators):
            inference_view = dec(inference_view)

    health_view = HealthView.as_view(f"{name}_health")
    modelinfo_view = ModelInfoView.as_view(
        f"{name}_modelinfo",
        modelinfo_fn=modelinfo_fn,
    )

    bp.add_url_rule("/", view_func=inference_view, methods=["POST"])
    bp.add_url_rule("/health", view_func=health_view, methods=["GET"])
    bp.add_url_rule("/modelinfo", view_func=modelinfo_view, methods=["GET"])

    return bp
