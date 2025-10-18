from cryptography.fernet import Fernet

from w.services.abstract_service import AbstractService


class FileService(AbstractService):
    @classmethod
    def save_encrypted_file(
        cls, file_name: str, file_content: bytes, encryption_key: str
    ) -> None:
        """
        Saves the given file content to the given file name.
        The file content is encrypted with the given encryption key.
        """
        f = Fernet(encryption_key)
        encrypted = f.encrypt(file_content)

        with open(file_name, "wb") as file:
            file.write(encrypted)

    @classmethod
    def load_encrypted_file(cls, file_name: str, encryption_key: str) -> bytes:
        """
        Loads the file content from the given file name.
        The file content is decrypted with the given encryption key.
        """
        f = Fernet(encryption_key)

        with open(file_name, "rb") as file:
            encrypted = file.read()

        return f.decrypt(encrypted)
