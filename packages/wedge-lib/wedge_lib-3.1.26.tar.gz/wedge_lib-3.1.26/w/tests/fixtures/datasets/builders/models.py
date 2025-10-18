from django.utils import timezone


class Example:
    def __init__(self, attribute_one, attribute_two):
        self.attribute_one = attribute_one
        self.attribute_two = attribute_two

    def __str__(self):
        return f"{self.attribute_one}/{self.attribute_two}"


class InternalDependencyOne:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"


class InternalDependencyTwo:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"


class ExampleWithInternalDependencies:
    def __init__(
        self,
        name,
        internal_one: InternalDependencyOne,
        internal_two: InternalDependencyTwo,
    ):
        self.name = name
        self.internal_one = internal_one
        self.internal_two = internal_two

    def __str__(self):
        return f"{self.name}"


class RelatedDependency:
    def __init__(self, name, example: ExampleWithInternalDependencies):
        self.name = name
        self.example = example

    def __str__(self):
        return f"{self.name}"


class ExampleWithAutoNow:
    def __init__(self, attribute_one):
        self.attribute_one = attribute_one
        self.attribute_date = timezone.now()

    def __str__(self):
        return f"{self.attribute_one}/{self.attribute_date}"


class FakeDjangoModel:
    def __init__(self, id, attribute_one):
        self.id = id
        self.pk = id
        self.attribute_one = attribute_one


class FakeDjangoModelWithForeignKey:
    def __init__(self, id, name, fk_one: FakeDjangoModel):
        self.id = id
        self.pk = id
        self.name = name
        self.fk_one = fk_one
