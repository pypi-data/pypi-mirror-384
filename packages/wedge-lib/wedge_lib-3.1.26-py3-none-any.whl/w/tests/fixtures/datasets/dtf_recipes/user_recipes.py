from w.django.tests.factories.auth_factories import UserFactory
from w.tests.fixtures.datasets.django_app.factory_boys import SsoUserFactory
from w.tests.fixtures.datasets.dtf_recipes import group_recipes

base_user = {"factory": UserFactory}
sso_user = {"factory": SsoUserFactory, "ref": "sso_user"}

user_with_one_group = {**base_user, "values": {"groups": [group_recipes.base_group]}}
