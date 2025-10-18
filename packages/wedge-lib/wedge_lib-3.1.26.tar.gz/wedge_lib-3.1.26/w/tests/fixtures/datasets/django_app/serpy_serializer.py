from w.serializers import serializer
from w.tests.fixtures.datasets.django_app import models


class SimpleSerializer(serializer.SerpySerializer):
    integer = serializer.IntField()
    string = serializer.StrField()
    date = serializer.DateField()


class InternalDependencyOneSerializer(serializer.SerpySerializer):
    class Meta:
        model = models.InternalDependencyOne

    id = serializer.Field()
    name = serializer.Field()


class InternalDependencyTwoSerializer(serializer.SerpySerializer):
    class Meta:
        model = models.InternalDependencyTwo

    id = serializer.Field()
    name = serializer.Field()


class ExampleSerializer(serializer.SerpySerializer):
    class Meta:
        model = models.ExampleWithFks

    id = serializer.Field()
    name = serializer.Field()
    internal_one = InternalDependencyOneSerializer()
    internal_two = InternalDependencyTwoSerializer()
