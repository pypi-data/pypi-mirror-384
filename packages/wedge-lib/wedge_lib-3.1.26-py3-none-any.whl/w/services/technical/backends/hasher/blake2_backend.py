import hashlib
import hmac
from typing import Optional

from django.conf import settings

from w.services.technical.backends.hasher.abstract_hasher_backend import (
    AbstractHasherBackend,
)


class Blake2Backend(AbstractHasherBackend):
    _settings_key = "HASH_SECRET_KEY"
    _secret_key: Optional[bytes] = None

    @classmethod
    def hash(cls, to_hash: str) -> str:
        hmac_blake2 = hmac.new(cls._get_secret_key(), to_hash.encode(), hashlib.blake2b)
        return hmac_blake2.hexdigest()

    @classmethod
    def _check_has_settings(cls) -> str:
        if hasattr(settings, cls._settings_key) is False:
            raise RuntimeError(f"{cls._settings_key} is missing in your settings")
        key = getattr(settings, cls._settings_key)
        if key:
            return key
        raise RuntimeError(
            f"{cls._settings_key} is empty, you must set a hash secret key"
        )

    @classmethod
    def _get_secret_key(cls) -> bytes:
        if cls._secret_key is None:
            key = cls._check_has_settings()
            cls._secret_key = key.encode()
        return cls._secret_key

    @classmethod
    def reset(cls):
        cls._secret_key = None
