from rest_framework import serializers

from w.drf.serializers.mixins import DrfValidatorSerializerMixin
from w.tests.fixtures.datasets.django_app import models


class SimpleCreateValidation(DrfValidatorSerializerMixin, serializers.Serializer):
    integer = serializers.IntegerField()
    string = serializers.CharField()
    date = serializers.DateField()


class WithContextValidation(SimpleCreateValidation):
    def validate_integer(self, value):
        return value * self.context["factor"]


class ExampleCreateValidation(DrfValidatorSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.ExampleWithInternalDependencies
        fields = "__all__"


class ExampleUpdateValidation(DrfValidatorSerializerMixin, serializers.ModelSerializer):
    class Meta:
        model = models.ExampleWithInternalDependencies
        fields = "__all__"
