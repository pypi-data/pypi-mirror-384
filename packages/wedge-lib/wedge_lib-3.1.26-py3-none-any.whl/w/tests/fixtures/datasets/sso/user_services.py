from django.contrib.auth.models import User

from w.drf.sso.sso_user_mixin import SsoUserMixin
from w.services.abstract_model_service import AbstractModelService
from w.tests.fixtures.datasets.django_app.models import SsoUser


class UserService(AbstractModelService):
    _model = User


class UserSsoService(SsoUserMixin, AbstractModelService):
    _model = SsoUser

    @classmethod
    def get_user_service(cls):
        return UserService
