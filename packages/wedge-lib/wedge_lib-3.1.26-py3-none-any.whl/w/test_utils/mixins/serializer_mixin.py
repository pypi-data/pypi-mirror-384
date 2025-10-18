from typing import Dict


class SerializerMixin:
    # serializer list
    _serializers: Dict = {}

    @classmethod
    def serialize(cls, serializer_key, queryset, many=False):
        if serializer_key not in cls._serializers:
            raise RuntimeError(
                f"{serializer_key} missing, add it to {__class__}._serializers"
            )
        serializer = cls._serializers[serializer_key](queryset, many=many)
        return serializer.data
