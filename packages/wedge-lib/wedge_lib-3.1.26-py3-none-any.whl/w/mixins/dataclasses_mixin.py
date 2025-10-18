from dataclasses import asdict, fields


class DataclassMixin:
    def to_dict(self):
        return asdict(self)  # noqa

    def __str__(self):
        return str(self.to_dict())

    @classmethod
    def list_fields(cls):
        return [f.name for f in fields(cls)]  # noqa
