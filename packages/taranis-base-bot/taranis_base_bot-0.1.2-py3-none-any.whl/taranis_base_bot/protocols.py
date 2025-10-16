from typing import Protocol, Any, Mapping, Sequence, runtime_checkable

JSONObj = Mapping[str, Any]
JSONList = Sequence[JSONObj]


@runtime_checkable
class Predictor(Protocol):
    """Interface for Predictor objects used in bots
    Need to implement predict method
    """

    model_name: str

    def predict(self, **kwargs: Any) -> JSONObj | JSONList: ...

    def modelinfo(self, **kwargs: Any) -> JSONObj | JSONList: ...
