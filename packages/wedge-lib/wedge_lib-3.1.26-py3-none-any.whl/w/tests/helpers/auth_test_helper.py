from contextlib import contextmanager

from w.test_utils.helpers import auth_test_helper


def get_generate_token_mock_config(token):
    # deprecated
    return auth_test_helper.get_generate_token_mock_config(token)


@contextmanager
def mock_generate_token(token):
    with auth_test_helper.mock_generate_token(token) as m:
        yield m
