from typing import Type

from w.services.abstract_service import AbstractService
from w.services.technical.backends.encryption.abstract_encryption_backend import (
    AbstractEncryptionBackend,
)
from w.services.technical.backends.encryption.fernet_backend import FernetBackend


class EncryptionService(AbstractService):
    _backend: Type[AbstractEncryptionBackend] = FernetBackend

    @classmethod
    def encrypt(cls, text_to_encrypt: str) -> str:
        return cls._backend.encrypt(text_to_encrypt)

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        return cls._backend.decrypt(encrypted_text)

    @classmethod
    def set_backend(cls, backend: Type[AbstractEncryptionBackend]):
        cls._backend = backend
