import pytest
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed

from w.data_test_factory.data_test_factory import DataTestFactory
from w.django.tests.django_testcase import DjangoTestCase
from w.drf.sso.sso_auth_backend import SsoAuthBackend
from w.services.technical.sso_service import SsoService
from w.tests.fixtures.datasets.dtf_recipes import user_recipes
from w.tests.helpers import sso_test_helper
from django.test.utils import override_settings

from w.tests.mixins.serializer_mixin import SerializerMixin
from w.tests.serializers.serpy_serializers import UserWithSsoUserTestSerializer


class TestSsoAuthBackend(SerializerMixin, DjangoTestCase):
    _serializers = {"user": UserWithSsoUserTestSerializer}

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.backend = SsoAuthBackend()
        SsoService.init()
        with sso_test_helper.mock_keycloak_admin_init():
            SsoService._init_keycloak_admin()
        dtf = DataTestFactory()
        cls.sso_user = dtf.build(
            {**user_recipes.sso_user, "values": {"sso_uuid": "fake-known-uuid"}}
        )

    """
    authenticate_credentials
    """

    def test_authenticate_credentials_with_invalid_token_raise_error(self):
        """Ensure invalid token raise AuthenticationFailed"""
        match = "Invalid or expired token."
        with sso_test_helper.valid_token_failure():
            with pytest.raises(AuthenticationFailed, match=match):
                self.backend.authenticate_credentials("invalid-token")

    def test_authenticate_credentials_with_missing_setting_raise_error(self):
        """Ensure method raide RuntimeError if USER_SERVICE settings missing"""
        sso_settings = {**settings.SSO}
        sso_settings.pop("USER_SERVICE")
        match = "'USER_SERVICE' is missing from SSO settings"
        with override_settings(SSO=sso_settings):
            with sso_test_helper.valid_token_success():
                with pytest.raises(RuntimeError, match=match):
                    self.backend.authenticate_credentials("valid-token")

    def test_authenticate_credentials_with_unknown_user_return_user(self):
        """Ensure authenticate with unknown user create it"""
        with sso_test_helper.valid_token_success(uuid="fake-unknown-uuid") as m:
            user, _ = self.backend.authenticate_credentials("valid-unknown-token")
        self.assert_equals_resultset(
            {"user": self.serialize("user", user), "mock_calls": self.get_mock_calls(m)}
        )

    def test_authenticate_credentials_with_success_return_user(self):
        """Ensure authenticate with known user update it"""
        with sso_test_helper.valid_token_success(uuid="fake-known-uuid") as m:
            user, _ = self.backend.authenticate_credentials("valid-known-token")
        self.assert_equals_resultset(
            {"user": self.serialize("user", user), "mock_calls": self.get_mock_calls(m)}
        )
