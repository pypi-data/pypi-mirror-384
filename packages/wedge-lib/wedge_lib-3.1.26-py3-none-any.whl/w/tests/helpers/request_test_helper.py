from contextlib import contextmanager

from w.test_utils.helpers import request_test_helper


@contextmanager
def request_failure(response: dict, method="get"):
    # deprecated
    with request_test_helper.request_failure(response, method) as m:
        yield m


@contextmanager
def request_success(response: dict, method="get"):
    # deprecated
    with request_test_helper.request_success(response, method) as m:
        yield m


@contextmanager
def mock_request(responses, method="get"):
    # deprecated
    with request_test_helper.mock_request(responses, method) as m:
        yield m


def get_response(**params):
    # deprecated
    return request_test_helper.get_response(**params)


def get_401_response(**params):
    # deprecated
    return request_test_helper.get_401_response(**params)


def get_400_response(**params):
    # deprecated
    return request_test_helper.get_400_response(**params)
