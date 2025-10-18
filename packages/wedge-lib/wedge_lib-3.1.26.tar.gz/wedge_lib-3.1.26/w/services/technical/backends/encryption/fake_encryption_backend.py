from w.services.technical.backends.encryption.abstract_encryption_backend import (
    AbstractEncryptionBackend,
)


class FakeEncryptionBackend(AbstractEncryptionBackend):
    @classmethod
    def encrypt(cls, text_to_encrypt: str) -> str:
        return text_to_encrypt.replace(" ", "µ")

    @classmethod
    def decrypt(cls, encrypted_text: str) -> str:
        return encrypted_text.replace("µ", " ")
