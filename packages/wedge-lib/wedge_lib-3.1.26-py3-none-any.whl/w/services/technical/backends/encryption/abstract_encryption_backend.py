from abc import ABC, abstractmethod


class AbstractEncryptionBackend(ABC):
    @classmethod
    @abstractmethod
    def encrypt(cls, text_to_encrypt: str) -> str:  # pragma: no cover
        pass

    @classmethod
    @abstractmethod
    def decrypt(cls, encrypted_text: str) -> str:  # pragma: no cover
        pass
