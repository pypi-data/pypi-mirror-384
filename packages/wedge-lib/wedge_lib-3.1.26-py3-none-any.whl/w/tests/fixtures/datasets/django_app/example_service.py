from w.services.abstract_model_service import AbstractModelService
from w.tests.fixtures.datasets.django_app import models


class ExampleService(AbstractModelService):
    _model = models.ExampleWithInternalDependencies
