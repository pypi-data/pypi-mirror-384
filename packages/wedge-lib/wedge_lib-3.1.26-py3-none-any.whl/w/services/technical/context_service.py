from typing import Optional

from w.exceptions import NotFoundError
from w.mixins.thread_mixin import ThreadMixin
from w.services.abstract_service import AbstractService
from w.services.technical.models.context import BaseContext


class ContextService(ThreadMixin, AbstractService):
    _registry = {}

    @classmethod
    def clear(cls):
        cls._registry = {}

    @classmethod
    def register(cls, key, context: BaseContext):
        if isinstance(context, BaseContext) is False:
            raise RuntimeError("Invalid context, you should inherit from BaseContext")

        current_thread_id = cls._get_current_thread_id()
        with cls._lock:
            cls._clean()
            if current_thread_id not in cls._registry:
                cls._registry[current_thread_id] = {}
            cls._registry[current_thread_id][key] = context

    @classmethod
    def get(cls, key) -> Optional[BaseContext]:
        current_thread_id = cls._get_current_thread_id()
        if current_thread_id not in cls._registry:
            return None
        return cls._registry.get(current_thread_id).get(key)

    @classmethod
    def check_exists(cls, key) -> BaseContext:
        context = cls.get(key)
        if context is None:
            raise NotFoundError(f"context '{key}' not found")
        return context

    @classmethod
    def _clean(cls) -> None:
        """
        Remove finished thread
        !! must be in a lock context !!
        """
        active_thread_ids = cls._list_active_thread_ids()
        cls._registry = {
            id: context
            for id, context in cls._registry.items()
            if id in active_thread_ids
        }
