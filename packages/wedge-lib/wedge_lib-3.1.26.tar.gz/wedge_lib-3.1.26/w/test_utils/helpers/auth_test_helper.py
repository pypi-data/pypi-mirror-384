from contextlib import contextmanager

from w.services.technical.auth_service import AuthService
from w.tests.helpers import service_test_helper


def get_generate_token_mock_config(token):
    return {
        "service": AuthService,
        "method_name": "generate_token",
        "return_value": token,
    }


@contextmanager
def mock_generate_token(token):
    mock = get_generate_token_mock_config(token)
    with service_test_helper.mock_service(**mock) as m:
        yield m
