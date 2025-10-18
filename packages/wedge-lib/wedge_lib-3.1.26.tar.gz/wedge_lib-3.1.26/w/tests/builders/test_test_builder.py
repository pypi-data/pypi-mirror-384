from w.django.tests.django_testcase import DjangoTestCase
from w.services.technical.date_service import DateService
from w.tests.fixtures.datasets.builders.builder_with_auto_now import BuilderWithAutoNow
from w.tests.fixtures.datasets.builders.builder_with_internal_dependencies import (
    BuilderWithInternalDependencies,
    InternalDependencyOneTestBuilder,
)
from w.tests.fixtures.datasets.builders.builder_with_related_dependencies import (
    BuilderWithRelatedDependencies,
)
from w.tests.fixtures.datasets.builders.simple_builder import SimpleBuilder


class TestTestBuilder(DjangoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    """
    simple_builder
    """

    def test_simple_builder_with_success(self):
        example = SimpleBuilder().build()
        example2 = SimpleBuilder().build(attribute_one="specific")
        assert example != example2
        assert example.attribute_one == "value1"
        assert example.attribute_two == "value2"
        assert example2.attribute_one == "specific"
        assert example2.attribute_two == "value2"

    """
    builder_with_internal_dependencies
    """

    def test_builder_with_internal_dependencies_with_success(self):
        actual = (
            BuilderWithInternalDependencies()
            .with_internal_one(name="name1")
            .with_internal_two(name="name2")
            .build()
        )
        assert actual.internal_one.name == "name1"
        assert actual.internal_two.name == "name2"

    def test_builder_with_internal_dependencies_with_reset_sequence(self):
        BuilderWithInternalDependencies.reset_sequence()
        actual = BuilderWithInternalDependencies().build()
        assert actual.name == "example_internal_name_1"
        assert actual.internal_one.name == "internal_one_name_1"
        assert actual.internal_two.name == "internal_two_name_1"

    def test_builder_with_internal_builder_with_success(self):
        actual = (
            BuilderWithInternalDependencies()
            .with_internal_one(
                builder=InternalDependencyOneTestBuilder().with_attrs(name="builder")
            )
            .with_internal_two(name="name2")
            .build()
        )
        assert actual.internal_one.name == "builder"
        assert actual.internal_two.name == "name2"

    """
    builder_with_related_dependencies
    """

    def test_builder_with_related_dependencies(self):
        BuilderWithInternalDependencies.reset_sequence()
        builder = BuilderWithRelatedDependencies()
        related_data = [{"name": "my_related_3"}, {"name": "my_related_4"}]
        actual = (
            builder.with_related_dependency(name="my_related_1")
            .with_related_dependency(name="my_related_2")
            .with_related_dependencies(related_data)
            .with_nb_related_dependencies(nb=2)
            .with_nb_related_dependencies(nb=2, name="same name")
            .build()
        )
        relateds = builder.get_related_dependency_built()
        assert len(relateds) == 8
        names = []
        for related in relateds:
            names.append(related.name)
            assert actual == related.example
        expected = [
            "my_related_1",
            "my_related_2",
            "my_related_3",
            "my_related_4",
            "related_name_4",
            "related_name_5",
            "same name",
            "same name",
        ]
        assert expected == names

    """
    builder_with_auto_now
    """

    def test_builder_with_auto_now_with_success(self):
        example = BuilderWithAutoNow().with_today_is("2018-05-05").build()
        example2 = (
            BuilderWithAutoNow()
            .with_today_is("2007-07-07")
            .build(attribute_one="specific")
        )
        assert example != example2
        assert example.attribute_one == "value1"
        assert DateService.to_mysql_date(example.attribute_date) == "2018-05-05"
        assert example2.attribute_one == "specific"
        assert DateService.to_mysql_date(example2.attribute_date) == "2007-07-07"

    """
    build_post_data
    """

    def test_build_post_data_with_simple_builder(self):
        actual = SimpleBuilder().build_post_data()
        self.assert_equals_resultset(actual)

    def test_build_post_data_with_internal_dependencies(self):
        BuilderWithInternalDependencies.reset_sequence(1)
        actual = BuilderWithInternalDependencies().build_post_data()
        self.assert_equals_resultset(actual)
