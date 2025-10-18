from w.django.tests.factories.auth_factories import UserFactory
from w.tests.builders.abstract_test_builder import AbstractTestBuilder


class UserTestBuilder(AbstractTestBuilder):
    _factories = {"user": UserFactory}
    _main_factory_key = "user"

    def build(self, **attrs):
        password = attrs.pop("password", None)
        user = super().build(**attrs)

        if password:
            user.set_password(password)
            user.save()

        return user
