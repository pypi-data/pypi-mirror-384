from w.drf.viewsets import ModelServiceViewSet


class ListModelServiceMixin:
    def list(self: ModelServiceViewSet, request, *args, **kwargs):
        return self.get_list_response(self.service.list())


class RetrieveModelServiceMixin:
    def retrieve(self: ModelServiceViewSet, request, *args, **kwargs):
        return self.get_retrieve_response()


class CreateModelServiceMixin:
    def create(self: ModelServiceViewSet, request, *args, **kwargs):
        instance = self.service.create(**self.check_is_valid())
        return self.get_create_response(instance)


class UpdateModelServiceMixin:
    def update(self: ModelServiceViewSet, request, *args, **kwargs):
        instance = self.service.check_by_pk(self.kwargs["pk"])
        return self.get_update_response(
            self.service.update(instance, **self.check_is_valid())
        )


class DeleteModelServiceMixin:
    def destroy(self: ModelServiceViewSet, request, *args, **kwargs):
        self.service.delete_by_pk(self.kwargs["pk"])
        return self.get_delete_response()
