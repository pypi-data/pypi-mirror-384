from dataclasses import dataclass
from datetime import datetime

from rest_framework.decorators import action

from w.drf.mixins import (
    ListModelServiceMixin,
    RetrieveModelServiceMixin,
    CreateModelServiceMixin,
    UpdateModelServiceMixin,
    DeleteModelServiceMixin,
)
from w.drf.viewsets import ViewSet, ModelServiceViewSet
from w.mixins.dataclasses_mixin import DataclassMixin
from w.tests.fixtures.datasets.django_app import serpy_serializer
from w.tests.fixtures.datasets.django_app import drf_serializer
from w.tests.fixtures.datasets.django_app.example_service import ExampleService


@dataclass
class Simple(DataclassMixin):
    integer: int
    string: str
    date: datetime.date


class SimpleViewset(ViewSet):
    serializers = {
        "default": serpy_serializer.SimpleSerializer,
        "create_validation": drf_serializer.SimpleCreateValidation,
        "with_context_validation": drf_serializer.WithContextValidation,
        "multiple_validation": drf_serializer.SimpleCreateValidation,
    }

    def create(self, request):
        validated_data = self.check_is_valid()
        return self.get_post_response(Simple(**validated_data))

    @action(methods=["post"], detail=False)
    def multiple(self, request, *args, **kwargs):
        validated_data = self.check_is_list_valid()
        expected_result = [Simple(**elt) for elt in validated_data]
        return self.get_post_response(expected_result)

    @action(methods=["post"], detail=False)
    def with_context(self, request, *args, **kwargs):
        context = {"factor": 10}
        validated_data = self.check_is_valid(context=context)
        return self.get_post_response(Simple(**validated_data))


class ModelViewset(
    DeleteModelServiceMixin,
    UpdateModelServiceMixin,
    CreateModelServiceMixin,
    RetrieveModelServiceMixin,
    ListModelServiceMixin,
    ModelServiceViewSet,
):
    serializers = {
        "default": serpy_serializer.ExampleSerializer,
        "create_validation": drf_serializer.ExampleCreateValidation,
        "update_validation": drf_serializer.ExampleUpdateValidation,
    }
    service = ExampleService

    @action(methods=["get"], detail=False, url_name="list-without-qp-filter")
    def list_without_query_params_filter(
        self: ModelServiceViewSet, request, *args, **kwargs
    ):
        return self.get_list_response(self.service.list(), filter_by_query_params=False)
