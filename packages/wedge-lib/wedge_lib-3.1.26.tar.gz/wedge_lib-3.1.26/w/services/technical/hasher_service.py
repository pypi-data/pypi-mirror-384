from typing import Type

from w.services.abstract_service import AbstractService
from w.services.technical.backends.hasher.abstract_hasher_backend import (
    AbstractHasherBackend,
)
from w.services.technical.backends.hasher.argon2_backend import Argon2Backend
from w.services.technical.backends.hasher.blake2_backend import Blake2Backend


class HasherService(AbstractService):
    _argon2_backend: Type[AbstractHasherBackend] = Argon2Backend
    _blake2_backend: Type[AbstractHasherBackend] = Blake2Backend

    @classmethod
    def argon2_hash(cls, to_hash: str) -> str:
        return cls._argon2_backend.hash(to_hash)

    @classmethod
    def blake2_hash(cls, to_hash: str) -> str:
        return cls._blake2_backend.hash(to_hash)

    @classmethod
    def reset(cls):  # pragma: no cover
        cls._argon2_backend = Argon2Backend
        cls._blake2_backend = Blake2Backend
