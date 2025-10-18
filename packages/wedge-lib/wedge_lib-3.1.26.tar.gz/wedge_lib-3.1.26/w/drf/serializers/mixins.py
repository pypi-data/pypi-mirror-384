class DrfValidatorSerializerMixin:
    def update(self, instance, validated_data):  # pragma: no cover
        raise RuntimeError("not intended to be used")

    def create(self, validated_data):  # pragma: no cover
        raise RuntimeError("not intended to be used")
