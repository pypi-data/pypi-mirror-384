from w.tests.builders.abstract_test_builder import AbstractTestBuilder
from w.tests.fixtures.datasets.builders.factory_boy import (
    ExampleWithInternalDependenciesFactory,
    InternalDependencyOneFactory,
    InternalDependencyTwoFactory,
    RelatedDependencyFactory,
)


class BuilderWithRelatedDependencies(AbstractTestBuilder):
    _factories = {
        "example": ExampleWithInternalDependenciesFactory,
        "internal_one": InternalDependencyOneFactory,
        "internal_two": InternalDependencyTwoFactory,
        "related_dependency": RelatedDependencyFactory,
    }
    _main_factory_key = "example"

    def with_internal_one(self, **attrs):
        self._set_foreign_key_factory_attrs("internal_one", attrs)
        return self

    def with_internal_two(self, **attrs):
        self._set_foreign_key_factory_attrs("internal_two", attrs)
        return self

    def with_related_dependency(self, **attrs):
        self._add_related_factory_attrs("related_dependency", attrs)
        return self

    def with_related_dependencies(self, list_attrs: list):
        self._set_related_factory_attrs("related_dependency", list_attrs)
        return self

    def with_nb_related_dependencies(self, nb, **attrs):
        self._set_nb_related_factory_attrs("related_dependency", nb, attrs)
        return self

    def get_related_dependency_built(self):
        return self._get_related_built("related_dependency")
