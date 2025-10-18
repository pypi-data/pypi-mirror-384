from w.tests.builders.abstract_test_builder import AbstractTestBuilder
from w.tests.fixtures.datasets.builders.factory_boy import ExampleWithAutoNowFactory


class BuilderWithAutoNow(AbstractTestBuilder):
    _factories = {"example": ExampleWithAutoNowFactory}
    _main_factory_key = "example"
