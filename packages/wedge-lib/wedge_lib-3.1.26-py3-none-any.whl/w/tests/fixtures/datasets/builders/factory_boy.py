import factory

from w.tests.fixtures.datasets.builders.models import (
    RelatedDependency,
    ExampleWithAutoNow,
    FakeDjangoModel,
    FakeDjangoModelWithForeignKey,
)
from w.tests.fixtures.datasets.django_app import models as django_models


class SimpleExampleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_models.Example

    attribute_one = "value1"
    attribute_two = "value2"


class InternalDependencyOneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_models.InternalDependencyOne

    name = factory.sequence(lambda n: f"internal_one_name_{n}")


class InternalDependencyTwoFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_models.InternalDependencyTwo

    name = factory.sequence(lambda n: f"internal_two_name_{n}")


class ExampleWithInternalDependenciesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = django_models.ExampleWithInternalDependencies

    name = factory.sequence(lambda n: f"example_internal_name_{n}")
    internal_one = factory.SubFactory(InternalDependencyOneFactory)
    internal_two = factory.SubFactory(InternalDependencyTwoFactory)


class RelatedDependencyFactory(factory.Factory):
    class Meta:
        model = RelatedDependency

    name = factory.sequence(lambda n: f"related_name_{n}")
    example = factory.SubFactory(InternalDependencyOneFactory)


class ExampleWithAutoNowFactory(factory.Factory):
    class Meta:
        model = ExampleWithAutoNow

    attribute_one = "value1"


class FakeDjangoModelFactory(factory.Factory):
    class Meta:
        model = FakeDjangoModel

    id = factory.Sequence(lambda n: n)
    attribute_one = factory.sequence(lambda n: f"attribute_one_{n}")


class FakeDjangoModelWithForeignKeyFactory(factory.Factory):
    class Meta:
        model = FakeDjangoModelWithForeignKey

    id = factory.Sequence(lambda n: n)
    attribute_one = factory.sequence(lambda n: f"name_{n}")
    fk_one = factory.SubFactory(FakeDjangoModelFactory)
