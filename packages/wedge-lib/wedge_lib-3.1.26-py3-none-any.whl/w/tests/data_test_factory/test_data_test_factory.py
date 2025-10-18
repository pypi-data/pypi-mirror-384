from w.data_test_factory.data_test_factory import DataTestFactory
from w.django.tests.django_testcase import DjangoTestCase
from w.tests.fixtures.datasets.data_test_factory import serializers
from w.tests.fixtures.datasets.django_app import dtf_models, dtf_recipes
from w.tests.mixins.serializer_mixin import SerializerMixin


class TestDataTestFactory(SerializerMixin, DjangoTestCase):
    _serializers = {
        "author": serializers.AuthorSerializer,
        "series": serializers.SeriesSerializer,
        "series_books": serializers.SeriesBooksSerializer,
        "book": serializers.BookSerializer,
        "book_characters": serializers.BookCharactersSerializer,
        "character": serializers.CharacterSerializer,
        "autonow_model": serializers.AutoNowModelSerializer,
        "one2one": serializers.One2OneCitySerializer,
    }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def setup_method(self, method):
        self.dtf = DataTestFactory()

    """
    build
    """

    def test_build_with_simple_model_return_model(self):
        """Ensure method succeed with simple model"""
        recipe_the_witcher = {
            **dtf_recipes.base_author,
            **{
                "ref": "the_witcher_author",
                "values": {"firstname": "Andrzej", "lastname": "Sapkowski"},
            },
        }
        base_author = self.dtf.build(dtf_recipes.base_author)
        the_witcher_author = self.dtf.build(recipe_the_witcher)
        assert base_author != the_witcher_author
        assert base_author.id == 1
        assert the_witcher_author.id == 2
        assert base_author.firstname == "fn_author_1"
        assert base_author.lastname == "ln_author_1"
        assert the_witcher_author.firstname == "Andrzej"
        assert the_witcher_author.lastname == "Sapkowski"

    def test_build_with_model_with_fk_return_model(self):
        """Ensure method succeed with model with foreign key"""
        actual = self.dtf.build(dtf_recipes.base_book)
        self.assert_equals_resultset(self.serialize("book", actual))

    def test_build_with_custom_fk_name_return_model(self):
        """Ensure method succeed with recipe set SubFactory attr"""
        recipe = {
            **dtf_recipes.base_book,
            "values": {
                "name": "Harry Potter and the Philosopher's Stone",
                "author": {
                    **dtf_recipes.base_author,
                    "values": {"firstname": "J.K.", "lastname": "Rowling"},
                },
            },
        }
        actual = self.dtf.build(recipe)
        self.assert_equals_resultset(self.serialize("book", actual))

    def test_build_with_auto_now_return_model(self):
        """Ensure we can mock auto now model attribute"""
        actual = self.dtf.build(dtf_recipes.base_autonow_model)
        self.assert_equals_resultset(self.serialize("autonow_model", actual))

    def test_build_with_multiple_author_recipe_return_list(self):
        """Ensure method succeed with nb attribute"""
        authors = self.dtf.build(dtf_recipes.base_author, nb=3)
        self.assert_equals_resultset(self.serialize("author", authors, many=True))

    def test_build_with_reverse_return_model(self):
        recipe_reverse = {
            **dtf_recipes.base_series,
            "values": {"books": [dtf_recipes.base_book, dtf_recipes.base_book]},
        }
        series = self.dtf.build(recipe_reverse)
        self.assert_equals_resultset(self.serialize("series_books", series))

    def test_build_with_many2many_return_model(self):
        """Ensure method succeed with many2many"""
        recipe_many2many = {
            **dtf_recipes.base_character,
            "values": {"books": [dtf_recipes.base_book, dtf_recipes.base_book]},
        }
        character = self.dtf.build(recipe_many2many)
        self.assert_equals_resultset(self.serialize("character", character))

    def test_build_with_context_return_model(self):
        """Ensure method succeed with context"""
        context = [
            dtf_recipes.base_series,
        ]
        recipe_with_context = {
            "context": context,
            **dtf_recipes.base_book,
            "ref": "series_book",
            "values": {"series": {"data_ref": "base_series"}},
        }
        books = self.dtf.build(recipe_with_context, nb=2)
        self.assert_equals_resultset(self.serialize("book", books, many=True))

    def test_build_with_multiple_ref_return_model(self):
        """Ensure method succeed with multiple data ref"""
        self.dtf.build(dtf_recipes.books_series_recipe, nb=2)
        self.assert_equals_resultset(
            self.serialize("book_characters", dtf_models.Book.objects.all(), many=True)
        )

    def test_build_with_from_db_and_fk_return_model(self):
        """Ensure method succeeds with 'from_db' used for a foreign key field"""
        self.dtf.build(dtf_recipes.base_author)
        recipe = {
            **dtf_recipes.base_book,
            "values": {
                "author": {
                    "from_db": {"model": dtf_models.Author, "selector": {"pk": 1}}
                }
            },
        }
        self.dtf.build(recipe)
        self.assert_equals_resultset(
            self.serialize("book_characters", dtf_models.Book.objects.all(), many=True)
        )

    def test_build_with_from_db_and_many2many_return_model(self):
        """Ensure method succeeds with 'from_db' used for many2many fields"""
        self.dtf.build(dtf_recipes.base_character, nb=2)
        recipe = {
            **dtf_recipes.base_book,
            "values": {
                "characters": [
                    {"from_db": {"model": dtf_models.Character, "selector": {"pk": 2}}},
                    {"from_db": {"model": dtf_models.Character, "selector": {"pk": 1}}},
                ]
            },
        }
        self.dtf.build(recipe)
        self.assert_equals_resultset(
            self.serialize("book_characters", dtf_models.Book.objects.all(), many=True)
        )

    def test_build_with_override_recipe_values_return_model(self):
        override_values = {
            "name": "Harry Potter and the Philosopher's Stone",
            "author": {
                **dtf_recipes.base_author,
                "values": {"firstname": "J.K.", "lastname": "Rowling"},
            },
        }

        actual = self.dtf.build(dtf_recipes.base_book, override_values=override_values)
        self.assert_equals_resultset(self.serialize("book", actual))

    def test_build_with_one2one_reverse_return_model(self):
        recipe = {
            **dtf_recipes.base_city,
            "values": {"one2one": dtf_recipes.base_one2one},
        }
        actual = self.dtf.build(recipe)
        self.assert_equals_resultset(self.serialize("one2one", actual.one2one))

    """
    today_is
    """

    def test_today_is_with_success_return_self(self):
        """Ensure method define force today to be asked date"""
        actual = self.dtf.today_is("2021-01-01 11:11:11").build(
            dtf_recipes.base_autonow_model
        )
        self.assert_equals_resultset(self.serialize("autonow_model", actual))

    """
    built_snapshots
    """

    def test_built_snapshots_with_success_return_dict(self):
        """Ensure method succeed"""
        self.dtf.build(dtf_recipes.books_series_recipe)
        self.assert_equals_resultset(self.dtf.built_snapshots())
