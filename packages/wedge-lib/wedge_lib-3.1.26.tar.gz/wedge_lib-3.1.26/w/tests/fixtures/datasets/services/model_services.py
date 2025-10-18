from w.services.abstract_model_service import AbstractModelService
from w.tests.fixtures.datasets.django_app import models, dtf_models


class ExampleService(AbstractModelService):
    _model = models.Example


class AuthorService(AbstractModelService):
    _model = dtf_models.Author


class BookService(AbstractModelService):
    _model = dtf_models.Book
