from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock

from keycloak import KeycloakAuthenticationError
from w.services.technical.models.sso import SsoValidToken
from w.services.technical.sso_service import SsoService
from w.tests.helpers import service_test_helper
from w.tests.mixins.testcase_mixin import TestCaseMixin


def _get_dataset(relative_dataset):
    current_dir = Path(__file__).parent
    dataset_filename = current_dir.joinpath(
        "../fixtures/datasets", relative_dataset
    ).resolve()
    return TestCaseMixin._get_dataset(dataset_filename.name, dataset_filename)


# noinspection PyProtectedMember
def _sso_instrospect_mock_attrs(dataset="introspect_success"):
    return {
        "service": SsoService,
        "method_name": "_sso_introspect",
        "return_value": _get_dataset(f"sso/{dataset}.json"),
    }


def _mock_get_or_create_user(created: bool = True):
    return {
        "service": SsoService,
        "method_name": "get_or_create_user",
        "return_value": (
            _get_dataset("sso_service/create_sso_user_with_success_return_dict.json"),
            created,
        ),
    }


def _get_user_token_mock_attrs(dataset="valid_user_token"):
    side_effect = (
        KeycloakAuthenticationError() if dataset == "invalid_user_token" else None
    )
    return {
        "service": SsoService,
        "method_name": "_get_user_token",
        "return_value": _get_dataset(f"sso/{dataset}.json"),
        "side_effect": side_effect,
    }


@contextmanager
def mock_keycloak_admin_init():
    keycloak_admin = Mock()
    mock_keycloak_admin = {
        "service": SsoService,
        "method_name": "_get_keycloak_admin",
        "return_value": keycloak_admin,
    }
    with service_test_helper.mock_service(**mock_keycloak_admin):
        yield keycloak_admin


@contextmanager
def mock_keycloak_initialize_admin():
    keycloak_admin = Mock()
    mock_keycloak_admin = {
        "service": SsoService,
        "method_name": "_initialize_admin",
        "return_value": keycloak_admin,
    }
    with service_test_helper.mock_service(**mock_keycloak_admin):
        yield keycloak_admin


@contextmanager
def valid_token_failure():
    mock_attrs = _sso_instrospect_mock_attrs("introspect_failure")
    with service_test_helper.mock_service(**mock_attrs) as m:
        yield m


@contextmanager
def sso_introspect_success():
    mock_attrs = _sso_instrospect_mock_attrs()
    with service_test_helper.mock_service(**mock_attrs) as m:
        yield m


@contextmanager
def mock_invalid_user_token():
    mock_attrs = _get_user_token_mock_attrs("invalid_user_token")
    with service_test_helper.mock_service(**mock_attrs) as m:
        yield m


@contextmanager
def mock_valid_user_token():
    mock_attrs = _get_user_token_mock_attrs()
    with service_test_helper.mock_service(**mock_attrs) as m:
        yield m


@contextmanager
def valid_token_success(uuid="fake-uuid"):
    fake_decoded_token = {
        "sub": uuid,
        "given_name": "fake-sub",
        "family_name": "fake-given_name",
        "username": "fake-family_name@fake-mail.com",
        "email": "fake-username@fake-mail.com",
        "resource_access": {
            "account": {
                "roles": ["manage-account", "manage-account-links", "view-profile"]
            }
        },
    }
    list_roles = [
        {
            "id": "2833c19b-13f1-4367-b128-4c440323ad1d",
            "name": "role_app1",
            "description": "Role App1",
            "composite": False,
            "clientRole": True,
            "containerId": "1a6113a1-2cfa-4f32-92c6-3359874104c0",
        }
    ]
    mock_attrs = {
        "service": SsoService,
        "method_name": "is_token_valid",
        "return_value": SsoValidToken(fake_decoded_token, list_roles=list_roles),
    }
    with service_test_helper.mock_service(**mock_attrs) as m:
        yield m


@contextmanager
def get_or_create_user_success(created: bool = True):
    with service_test_helper.mock_service(**_mock_get_or_create_user(created)) as m:
        yield m
