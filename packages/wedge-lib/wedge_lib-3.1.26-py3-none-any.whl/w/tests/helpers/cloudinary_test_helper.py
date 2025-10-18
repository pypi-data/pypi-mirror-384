from contextlib import contextmanager
from pathlib import Path
from typing import ContextManager
from unittest.mock import Mock, patch

from w.tests.mixins.testcase_mixin import TestCaseMixin


@contextmanager
def mock_cloudinary_upload() -> ContextManager[Mock]:
    with patch("cloudinary.uploader.upload") as mock:
        yield mock


@contextmanager
def mock_cloudinary_delete() -> ContextManager[Mock]:
    with patch("cloudinary.api.delete_resources") as mock:
        yield mock


def _get_dataset(relative_dataset):
    current_dir = Path(__file__).parent
    dataset_filename = current_dir.joinpath(
        "../fixtures/datasets", relative_dataset
    ).resolve()
    return TestCaseMixin._get_dataset(dataset_filename.name, dataset_filename)
