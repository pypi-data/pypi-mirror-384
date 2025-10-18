from contextlib import contextmanager

from w.services.abstract_service import AbstractService
from w.test_utils.helpers import service_test_helper


def get_target(config):
    # deprecated
    return service_test_helper.get_target(config)


@contextmanager
def mock_services(mock_configs):
    # deprecated
    with service_test_helper.mock_services(mock_configs) as m:
        yield m


@contextmanager
def mock_service(
    service: AbstractService, method_name: str, return_value=None, side_effect=None
):
    # deprecated
    with service_test_helper.mock_service(
        service, method_name, return_value, side_effect
    ) as m:
        yield m
