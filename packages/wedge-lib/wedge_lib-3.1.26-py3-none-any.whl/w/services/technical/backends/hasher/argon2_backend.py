from argon2 import PasswordHasher

from w.services.technical.backends.hasher.abstract_hasher_backend import (
    AbstractHasherBackend,
)


class Argon2Backend(AbstractHasherBackend):
    _ph = PasswordHasher()

    @classmethod
    def hash(cls, to_hash: str) -> str:
        return cls._ph.hash(to_hash)
