import json
from pathlib import Path
from typing import Any


class StubMixin:
    _datasets_dir: Path | None = None
    _calls = {}
    _stub = {}

    @classmethod
    def reset_stub(cls):
        cls._calls = {}
        cls._stub = {}

    @classmethod
    def list_calls(cls):
        return cls._calls

    @classmethod
    def call_count(cls, method) -> int:
        return len([c for c in cls._calls if method in c])

    @classmethod
    def stub(
        cls, method, response: Any | None = None, responses: list | None = None
    ):  # pragma: no cover
        if responses is None:
            cls._stub[method] = [response]
            return None
        cls._stub[method] = responses

    def stub_with_dataset(self, method, dataset_type="success"):
        self._stub[method] = [self._load_dataset(method, dataset_type)]

    @classmethod
    def _call_stub(cls, default_response=None) -> Any:
        method_name, args = cls._get_caller()

        cls._register_call(method_name, args)
        if method_name in cls._stub:
            return cls._render_stub(method_name)

        return cls._get_default_response(method_name, default_response)

    @classmethod
    def _register_call(cls, method, payload):
        if method not in cls._calls:
            cls._calls[method] = []
        cls._calls[method].append(payload)

    @staticmethod
    def _get_caller():
        import inspect

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        method_name = calframe[2][3]
        payload = calframe[2].frame.f_locals
        payload.pop("self", None)
        payload.pop("cls", None)
        return method_name, payload

    @classmethod
    def _render_stub(cls, method):  # pragma: no cover
        response = cls._stub[method].pop(0)
        if not cls._stub[method]:
            cls._stub.pop(method)
        if isinstance(response, Exception):
            raise response
        return response

    @classmethod
    def _get_default_response(
        cls, method: str, default_response: Any = None
    ) -> Any | None:
        if default_response:
            return default_response

        if cls._datasets_dir is None:
            return None

        dataset = cls._load_dataset(method=method)
        return dataset

    @classmethod
    def _load_dataset(cls, method: str, dataset: str = "success"):
        filename = cls._get_dataset_path(cls._get_dataset_name(method, dataset))
        if not filename.exists():
            raise RuntimeError(f"Dataset {filename} not found")
        with open(filename, "r") as file:
            return json.load(file)

    @classmethod
    def _get_dataset_name(cls, method: str, dataset: str) -> str:
        return f"{method}_{dataset}.json"

    @classmethod
    def _get_dataset_path(cls, dataset) -> Path:
        return cls._datasets_dir.joinpath(dataset).resolve()
