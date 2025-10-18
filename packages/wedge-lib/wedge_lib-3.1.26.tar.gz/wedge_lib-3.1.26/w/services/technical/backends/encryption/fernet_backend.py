from typing import Optional

from cryptography.fernet import Fernet
from django.conf import settings

from w.services.technical.backends.encryption.abstract_encryption_backend import (
    AbstractEncryptionBackend,
)


class FernetBackend(AbstractEncryptionBackend):
    _settings_key = "ENCRYPTION_FERNET_KEY"
    _cypher: Optional[Fernet] = None

    @classmethod
    def encrypt(cls, text_to_encrypt: str) -> str:
        cypher = cls._get_cypher()
        return cypher.encrypt(text_to_encrypt.encode()).decode()

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        cypher = cls._get_cypher()
        return cypher.decrypt(encrypted_text.encode()).decode()

    @classmethod
    def reset(cls):
        cls._cypher = None

    @classmethod
    def _check_has_settings(cls) -> str:
        if hasattr(settings, cls._settings_key) is False:
            raise RuntimeError(f"{cls._settings_key} is missing in your settings")
        key = getattr(settings, cls._settings_key)
        if key:
            return key
        raise RuntimeError(f"{cls._settings_key} is empty, you must set a Fernet key")

    @classmethod
    def _get_cypher(cls) -> Fernet:
        if cls._cypher is None:
            key = cls._check_has_settings()
            cls._cypher = Fernet(key)
        return cls._cypher
