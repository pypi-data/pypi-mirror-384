import factory
from faker.generator import random

from w.django.tests.factories.auth_factories import UserFactory
from w.tests.fixtures.datasets.django_app import models


class SsoUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.SsoUser

    sso_uuid = factory.Sequence(lambda n: f"fake-sso-uuid-{n}")
    list_apps = factory.LazyFunction(lambda: random.choices(["app1", "app2", "app3"]))
    user = factory.SubFactory(UserFactory)
