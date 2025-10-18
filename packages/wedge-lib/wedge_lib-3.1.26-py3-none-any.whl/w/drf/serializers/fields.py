from rest_framework import serializers


class StrictBooleanField(serializers.BooleanField):
    def to_internal_value(self, data):
        if data == "":
            data = None
        if data in ("true", "True", "1"):
            data = True
        if data in ("false", "False", "0"):
            data = False

        if self.required and data is None:
            raise serializers.ValidationError("This field may not be blank.")

        if data not in (False, True):
            raise serializers.ValidationError("This field must be a boolean.")

        return data
