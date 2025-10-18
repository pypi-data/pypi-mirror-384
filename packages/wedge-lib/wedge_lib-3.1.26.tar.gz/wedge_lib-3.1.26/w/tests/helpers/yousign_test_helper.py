from contextlib import contextmanager
from unittest.mock import patch

from w.services.technical.yousign_service import YousignService


def get_target(method_name):
    return YousignService.get_patch_target(method_name)


@contextmanager
def start_procedure_success(return_value):
    with patch(get_target("start_procedure"), return_value=return_value) as m:
        yield m


@contextmanager
def start_procedure_yousign_failure():
    side_effect = RuntimeError("yousign api failed")
    with patch(get_target("start_procedure"), side_effect=side_effect) as m:
        yield m


@contextmanager
def download_signature_request_document_yousign_success():
    return_value = bytes("fake signed document", "utf-8")
    with patch(
        get_target("download_signature_request_document"), return_value=return_value
    ) as m:
        yield m


@contextmanager
def download_signature_request_document_yousign_failure():
    side_effect = RuntimeError("yousign download api failed")
    with patch(
        get_target("download_signature_request_document"), side_effect=side_effect
    ) as m:
        yield m
