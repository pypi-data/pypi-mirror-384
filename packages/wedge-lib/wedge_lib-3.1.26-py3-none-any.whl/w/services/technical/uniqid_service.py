from abc import ABC, abstractmethod
from typing import Self, Type
from uuid import uuid4

from ulid import ULID

from w.services.abstract_service import AbstractService


class AbstractUniqIdGenerator(ABC):
    @abstractmethod
    def next_id(self, name: str | None = None) -> str: ...  # pragma: no cover


class AbstractFakeUniqIdGenerator(AbstractUniqIdGenerator, ABC):  # pragma: no cover
    _key_length: int
    _prefix: str

    def __init__(self, start_id=1):
        self._start: int = start_id - 1
        self._session: dict[str, int] = {"default": self._start}

    def reset(self, start_id=1) -> Self:
        self._start = start_id - 1
        self._session = {"default": self._start}
        return self

    def next_id(self, name: str | None = None) -> str:
        if name is None:
            name = "default"
        if name not in self._session:
            name_length = len(self._sanitize_name(name))
            start_length = len(str(self._start))
            total_length = 10 + name_length + start_length
            if total_length > 26:
                raise ValueError(
                    f"Uniq Id will be too long {total_length} > 26, reduce start_id "
                    f"({self._start}={start_length}) or name ({name}={name_length})"
                )
            self._session[name] = self._start

        self._session[name] += 1
        return self._format_id(name)

    def _format_id(self, name: str) -> str:
        if name == "default":
            pad = self._key_length - 8
            return f"{self._prefix}{self._session[name]:>0{pad}}"

        postfix = self._sanitize_name(name)
        pad = (self._key_length - 10) - len(postfix)
        id = f"{self._prefix}-{postfix}-{self._session[name]:>0{pad}}"
        # noinspection Assert
        assert len(id) == self._key_length, (
            f"id length must be {self._key_length}, got {len(id)}"
        )
        return id

    @staticmethod
    def _sanitize_name(name: str) -> str:
        return name.replace("_", "").upper()


class FakeUuidGenerator(AbstractFakeUniqIdGenerator):
    _key_length = 36
    _prefix = "FAKEUUID"


class UuidGenerator(AbstractUniqIdGenerator):  # pragma: no cover
    def next_id(self, name: str | None = None) -> str:
        return str(uuid4())


class FakeUlidGenerator(AbstractFakeUniqIdGenerator):
    _key_length = 26
    _prefix = "FAKEULID"


class UlidGenerator(AbstractUniqIdGenerator):
    def next_id(self, name: str | None = None) -> str:
        return str(ULID())


class UniqIdService(AbstractService):
    _generator: AbstractUniqIdGenerator = UlidGenerator()
    _fake_generator: Type[AbstractFakeUniqIdGenerator] = FakeUlidGenerator

    @classmethod
    def get(cls, name: str | None = None):
        return cls._generator.next_id(name)

    @classmethod
    def set_generator(cls, generator: AbstractUniqIdGenerator):
        cls._generator = generator

    @classmethod
    def set_fake_generator(
        cls, start_id=1, fake_generator: AbstractFakeUniqIdGenerator | None = None
    ):
        cls._generator = fake_generator or cls._fake_generator(start_id)

    @classmethod
    def reset_fake_generator(cls, start_id=1):
        if isinstance(cls._generator, AbstractFakeUniqIdGenerator):
            cls._generator.reset(start_id)
            return None
        raise RuntimeError("Current generator must be FakeGenerator")

    @classmethod
    def get_generator(cls) -> AbstractUniqIdGenerator:
        return cls._generator

    @classmethod
    def clear(cls):
        cls._generator = UlidGenerator()
