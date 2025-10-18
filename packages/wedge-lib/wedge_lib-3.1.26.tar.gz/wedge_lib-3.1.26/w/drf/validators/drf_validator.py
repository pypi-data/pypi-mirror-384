from rest_framework import serializers


class DrfValidator(serializers.Serializer):
    def update(self, instance, validated_data):
        raise RuntimeError("Forbidden, only for validation")

    def create(self, validated_data):
        raise RuntimeError("Forbidden, only for validation")
