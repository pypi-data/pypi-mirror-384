from enum import Enum
from typing import Type

from django.contrib.auth.models import User
import json
from django.db import models
from pyzstd import decompress, compress

from w.services.technical.json_service import JsonService


class TextChoices(models.TextChoices):
    @classmethod
    def list_codes(cls):
        return [code for code, label in cls.choices]


class AbstractCreatedModel(models.Model):
    created_at = models.DateTimeField("crée le", auto_now_add=True)

    class Meta:
        abstract = True


class AbstractCreatedUpdatedModel(AbstractCreatedModel):
    updated_at = models.DateTimeField("maj le", auto_now=True)

    class Meta:
        abstract = True


class AbstractSsoUser(AbstractCreatedUpdatedModel):
    sso_uuid = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    list_apps = models.JSONField()
    user = models.OneToOneField(User, related_name="sso_user", on_delete=models.CASCADE)

    class Meta:
        abstract = True


class Reference(AbstractCreatedUpdatedModel):
    code = models.CharField(max_length=20, primary_key=True)
    label = models.CharField(max_length=100)

    class Meta:
        abstract = True
        ordering = ["label"]

    def __str__(self):
        return self.label


class CompressedJsonField(models.BinaryField):
    description = "Compress field - specially used for logs fields"

    def get_db_prep_value(self, value, connection, prepared=False):
        return compress(JsonService.dump(value).encode("utf-8"))

    def from_db_value(self, value, expression, connection):
        if value is None:
            return value
        value = decompress(bytes(value)).decode("utf8")
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value


class CompressedTextField(models.BinaryField):
    description = "Compress Text field"

    def get_db_prep_value(self, value, connection, prepared=False):
        if value is not None:
            return compress(value.encode("utf-8"))
        return value

    def to_python(self, value):
        return value

    def from_db_value(self, value, expression, connection):
        if value is not None:
            return decompress(bytes(value)).decode("utf-8")
        return value


class EnumStrField(models.CharField):
    def __init__(self, enum: Type[Enum], *args, **kwargs):
        kwargs.setdefault("max_length", max(len(e.value) for e in enum))
        self.enum = enum
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection, *args):
        if value is None:
            return None
        return self.enum(value)

    def to_python(self, value):
        if value is None or value == "":
            return None
        if isinstance(value, self.enum):
            return value.value
        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs["enum"] = self.enum
        kwargs.pop("choices", None)
        if "default" in kwargs:
            if hasattr(kwargs["default"], "value"):
                kwargs["default"] = kwargs["default"].value

        return name, path, args, kwargs
