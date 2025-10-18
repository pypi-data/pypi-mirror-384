from w.data_test_factory.data_test_factory import DataTestFactory
from w.django.tests.django_testcase import DjangoTestCase
from w.tests.fixtures.datasets.dtf_recipes import user_recipes
from w.tests.fixtures.datasets.sso.user_services import UserSsoService
from w.tests.helpers import sso_test_helper
from w.tests.mixins.serializer_mixin import SerializerMixin
from w.tests.serializers import serpy_serializers


class TestSsoUserMixin(SerializerMixin, DjangoTestCase):
    _serializers = {
        "user": serpy_serializers.UserSsoTestSerializer,
    }

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        dtf = DataTestFactory()
        cls.sso_user = dtf.build(
            {**user_recipes.sso_user, "values": {"sso_uuid": "fake-known-uuid"}}
        )
        cls.new_data = {
            "username": "new@fake.com",
            "email": "new@fake.com",
            "first_name": "new_first",
            "last_name": "new_last",
            "list_apps": ["newapp1", "newapp3"],
        }

    """
    remap_sso2django_user
    """

    def test_remap_sso2django_user_with_success_return_dict(self):
        """Ensure method succeed"""
        data = {
            "email": "the Email",
            "username": "the Username",
            "firstName": "the Firstname",
            "lastName": "the Lastname",
        }
        actual = UserSsoService.remap_sso2django_user(data)
        self.assert_equals_resultset(actual)

    """
    get_by_uuid
    """

    def test_get_by_uuid_with_success_return_user(self):
        """Ensure method succeed"""
        actual = UserSsoService.get_by_uuid(self.sso_user.sso_uuid)
        self.assert_equals_resultset(self.serialize("user", actual))

    """
    get_by_uuid_if_exist
    """

    def test_get_by_uuid_if_exist_with_unkown_uuid_return_none(self):
        """Ensure method return None if user does not exist"""
        assert UserSsoService.get_by_uuid_if_exist("unknown-uuid") is None

    def test_get_by_uuid_if_exist_with_success_return_user(self):
        """Ensure method succeed"""
        actual = UserSsoService.get_by_uuid_if_exist(self.sso_user.sso_uuid)
        self.assert_equals_resultset(self.serialize("user", actual))

    """
    create_or_update_by_uuid
    """

    def test_create_or_update_by_uuid_with_not_found_user_return_user(self):
        """Ensure method create unknown user"""
        actual, created = UserSsoService.create_or_update_by_uuid(
            "new-user-uuid", self.new_data
        )
        assert created is True
        self.assert_equals_resultset(self.serialize("user", actual))

    def test_create_or_update_by_uuid_with_existing_user_return_user(self):
        """Ensure method update known user"""
        data = {
            "username": "upd@fake.com",
            "email": "upd@fake.com",
            "first_name": "upd_first",
            "last_name": "upd_last",
            "list_apps": ["updapp1"],
        }
        actual, created = UserSsoService.create_or_update_by_uuid(
            self.sso_user.sso_uuid, data
        )
        assert created is False
        self.assert_equals_resultset(self.serialize("user", actual))

    """
    get_or_create_sso_user
    """

    def test_get_or_create_sso_user_with_no_existing_sso_user_return_sso_user(self):
        """Ensure method succeeds and creation indicator is True"""
        with sso_test_helper.get_or_create_user_success() as m:
            actual, created = UserSsoService.get_or_create_sso_user(
                self.sso_user.user, "a-password", ["newapp1", "newapp3"]
            )
        assert created is True
        self.assert_equals_resultset(
            {"actual": actual, "mock_calls": self.get_mock_calls(m)}
        )
        self.save_as_dataset(
            "sso_service/get_or_create_sso_user_with_success_return_dict.json", actual
        )

    def test_get_or_create_sso_user_with_existing_sso_user_return_sso_user(self):
        """Ensure method succeeds and creation indicator is False"""
        with sso_test_helper.get_or_create_user_success(created=False) as m:
            actual, created = UserSsoService.get_or_create_sso_user(
                self.sso_user.user, "a-password", ["newapp1", "newapp3"]
            )
        assert created is False
        self.assert_equals_resultset(
            {"actual": actual, "mock_calls": self.get_mock_calls(m)}
        )
