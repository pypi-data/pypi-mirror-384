from w.data_test_factory.data_test_factory import DataTestFactory
from w.django import utils
from w.django.tests.django_testcase import DjangoTestCase
from w.tests.fixtures.datasets.django_app import dtf_recipes


class TestDjangoUtils(DjangoTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    """
    model_to_dict
    """

    def test_model_to_dict_with_fk_return_dict(self):
        dtf = DataTestFactory()
        model = dtf.build(dtf_recipes.base_author)
        self.assert_equals_resultset(utils.model_to_dict(model))

    def test_model_to_dict_with_many2many_return_dict(self):
        recipe_many2many = {
            **dtf_recipes.base_character,
            "values": {"books": [dtf_recipes.base_book, dtf_recipes.base_book]},
        }
        dtf = DataTestFactory()
        model = dtf.build(recipe_many2many)
        self.assert_equals_resultset(utils.model_to_dict(model))

    def test_model_to_dict_with_success_return_dict(self):
        dtf = DataTestFactory()
        model = dtf.build(dtf_recipes.books_series_recipe)
        self.assert_equals_resultset(utils.model_to_dict(model))
