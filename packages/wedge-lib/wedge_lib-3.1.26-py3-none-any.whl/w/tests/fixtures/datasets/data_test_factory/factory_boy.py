import factory
from w.tests.fixtures.datasets.django_app import dtf_models


class CityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.City

    name = factory.sequence(lambda n: f"city_{n}")


class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.Author

    firstname = factory.sequence(lambda n: f"fn_author_{n}")
    lastname = factory.sequence(lambda n: f"ln_author_{n}")
    birth_city = factory.SubFactory(CityFactory)


class SeriesFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.Series

    name = factory.sequence(lambda n: f"series_{n}")


class DepartmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.Department

    name = factory.sequence(lambda n: f"dpt_{n}")


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.Book

    name = factory.sequence(lambda n: f"book_{n}")
    author = factory.SubFactory(AuthorFactory)


class BookSeriesFactory(BookFactory):
    series = factory.SubFactory(SeriesFactory)


class CharacterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.Character

    firstname = factory.sequence(lambda n: f"fn_character_{n}")
    lastname = factory.sequence(lambda n: f"ln_character_{n}")


class AutoNowModelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.AutoNowModel


class One2OneCityFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = dtf_models.One2OneCity

    city = factory.SubFactory(CityFactory)
