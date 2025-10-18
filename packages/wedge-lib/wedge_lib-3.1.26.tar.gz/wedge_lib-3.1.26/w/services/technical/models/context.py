import threading
from abc import ABC, abstractmethod

from w.services.technical.date_service import DateService


class BaseContext(ABC):  # pragma: no cover
    def __init__(self):
        self.thread_id = threading.currentThread().ident
        self._date_create = DateService.to_mysql_datetime()

    @abstractmethod
    def to_dict(self): ...
