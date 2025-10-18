from w.tests.builders.abstract_test_builder import AbstractTestBuilder
from w.tests.fixtures.datasets.builders.factory_boy import (
    ExampleWithInternalDependenciesFactory,
    InternalDependencyOneFactory,
    InternalDependencyTwoFactory,
)


class InternalDependencyOneTestBuilder(AbstractTestBuilder):
    _factories = {
        "internal_one": InternalDependencyOneFactory,
    }
    _main_factory_key = "internal_one"


class BuilderWithInternalDependencies(AbstractTestBuilder):
    _factories = {
        "example": ExampleWithInternalDependenciesFactory,
        "internal_one": InternalDependencyOneFactory,
        "internal_two": InternalDependencyTwoFactory,
    }
    _main_factory_key = "example"

    def with_internal_one(self, builder=None, **attrs):
        if builder:
            self._set_foreign_key_builder("internal_one", builder)
        else:
            self._set_foreign_key_factory_attrs("internal_one", attrs)
        return self

    def with_internal_two(self, **attrs):
        self._set_foreign_key_factory_attrs("internal_two", attrs)
        return self
