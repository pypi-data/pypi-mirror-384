import unicodedata

from django.core.signing import Signer, BadSignature

from w.exceptions import ValidationError
from w.services.abstract_service import AbstractService


class StringService(AbstractService):
    _signer = None

    @classmethod
    def strip_accents(cls, txt) -> str:
        """
        Replace the characters with accents in txt by their normal form.

        Args:
            txt(str): text to clean

        Returns:
            str: cleaned text
        """
        return "".join(
            (
                c
                for c in unicodedata.normalize("NFD", txt)
                if unicodedata.category(c) != "Mn"
            )
        )

    @classmethod
    def clean(cls, txt, options=None) -> str:
        """
        Clean the provided text by :
            - applying all the replacements specified in options, if any
            - removing space from both left and right,
            - converting all uppercase characters into lower ones
            - removing all accents

        Args:
            txt(str): text to clean
            options(dict): substring replacements :
                {"old_substring": "new_substring", ...}

        Returns:
            str: cleaned text
        """
        cleaned_txt = txt
        if options is not None:
            for old, new in options.items():
                cleaned_txt = cleaned_txt.replace(old, new)
        return cls.strip_accents(cleaned_txt.strip().lower())

    @classmethod
    def sign(cls, value: int | str) -> str:
        cls._check_is_initialized()
        return cls._signer.sign(value)

    @classmethod
    def unsign(cls, signed_value: str) -> str:
        cls._check_is_initialized()
        try:
            return cls._signer.unsign(signed_value)
        except BadSignature:
            raise ValidationError(f"'{signed_value}' has invalid signature")

    @classmethod
    def _check_is_initialized(cls) -> None:
        if cls._signer is None:
            cls._signer = Signer()
