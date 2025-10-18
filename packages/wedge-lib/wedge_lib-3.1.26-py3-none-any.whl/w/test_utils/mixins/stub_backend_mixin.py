import logging
from contextlib import contextmanager
from functools import wraps
from typing import Any, Optional, List, ContextManager

from pydantic import BaseModel
from w.services.technical.json_service import JsonService

logger = logging.getLogger(__name__)


class StubBackendMixin:
    _stub = {}
    _calls = []
    _fixtures_path = None
    _dataset_dir = None

    @classmethod
    def reset_stub(cls):
        cls._calls = []
        cls._stub = {}

    @classmethod
    def list_calls(cls):
        return cls._calls

    @classmethod
    def call_count(cls, method) -> int:
        return len([c for c in cls._calls if method in c])  # pragma: no cover

    @classmethod
    def stub(cls, method: str, response: Any):  # pragma: no cover
        cls._stub[method] = [response]

    @classmethod
    def stub_many(cls, method: str, responses: List[Any]):  # pragma: no cover
        cls._stub[method] = responses

    @classmethod
    def stub_with_dataset(cls, method: str, dataset_type: str = "success"):
        cls.stub(method, cls._load_dataset(method, dataset_type=dataset_type))

    @classmethod
    def _call_stub(cls, response_none=False, data: BaseModel = None) -> Any:
        method_name, args = cls._get_caller()

        cls._register_call(method_name, args)
        if method_name in cls._stub:
            return cls._render_stub(method_name)

        return cls._get_default_response(method_name, response_none, args, data)

    @classmethod
    def _register_call(cls, method, payload):
        cls._calls.append({method: payload})

    @classmethod
    def _get_default_response(
        cls, method: str, response_none: bool, args=None, data: BaseModel = None
    ) -> Optional[dict]:
        logger.info(f"{cls.__name__}::{method} with args {args}")

        if response_none:
            return None

        dataset = cls._load_dataset(method=method, args=args)

        if data is None:
            return dataset

        data_dict = data.model_dump(exclude_unset=True)
        return {key: data_dict.get(key, value) for key, value in dataset.items()}

    @classmethod
    def _load_dataset(cls, method: str, dataset_type: str = "success", args=None):
        dataset_name = cls._get_dataset_name(
            method=method, dataset_type=dataset_type, args=args
        )
        filename = f"{cls._fixtures_path}/{dataset_name}"
        return JsonService.load_from_file(filename)

    @classmethod
    def _get_dataset_name(cls, method: str, dataset_type: str = "success", args=None):
        if args and "pagination" in args:
            page = args["pagination"].page
            return f"{method}_page{page}.json"
        return f"{method}_{dataset_type}.json"

    @classmethod
    def _render_stub(cls, method):  # pragma: no cover
        stubs = cls._stub.get(method)
        response = stubs.pop(0)
        if not stubs:
            del cls._stub[method]
        if isinstance(response, Exception):
            raise response
        return response

    @staticmethod
    def _get_caller():
        import inspect

        curframe = inspect.currentframe()
        calframe = inspect.getouterframes(curframe, 2)
        method_name = calframe[2][3]
        args = {
            arg: calframe[2].frame.f_locals[arg]
            for arg in calframe[2].frame.f_locals
            if arg != "cls" and arg.startswith("_") is False
        }
        return method_name, args

    @classmethod
    @contextmanager
    def change_result(cls, method_name: str, result: Any) -> ContextManager:
        target = getattr(cls, method_name)

        @wraps(target)
        def overwrite(*args, **kwargs):
            target(*args, **kwargs)
            return result

        setattr(cls, method_name, overwrite)

        try:
            yield cls
        finally:
            setattr(cls, method_name, target)
