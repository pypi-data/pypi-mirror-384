from abc import ABC


class AbstractHasherBackend(ABC):
    @classmethod
    def hash(cls, to_hash: str) -> str:  # pragma: no cover
        pass
