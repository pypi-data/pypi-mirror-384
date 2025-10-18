from w.services.technical.backends.hasher.abstract_hasher_backend import (
    AbstractHasherBackend,
)


class FakeHasherBackend(AbstractHasherBackend):
    @classmethod
    def hash(cls, to_hash: str) -> str:
        return "*" * len(to_hash)
