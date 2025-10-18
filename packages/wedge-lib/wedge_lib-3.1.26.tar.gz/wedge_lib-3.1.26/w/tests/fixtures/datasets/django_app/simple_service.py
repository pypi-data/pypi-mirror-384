from w.services.abstract_service import AbstractService


class SimpleService(AbstractService):
    @classmethod
    def create(cls, **attrs):
        return attrs
