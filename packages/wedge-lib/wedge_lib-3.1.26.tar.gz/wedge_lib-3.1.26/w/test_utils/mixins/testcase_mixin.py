import inspect
import json
import os
from os import path
from pathlib import Path
from typing import List, Type

import factory.random
from faker import Faker

from w.services.technical.filesystem_service import FilesystemService
from w.services.technical.uniqid_service import UniqIdService
from w.tests.builders.abstract_test_builder import AbstractTestBuilder


class TestCaseMixin:
    """Mixin to handle common test functionalities"""

    _fixture_dir = None
    _w_fixture_dir = None

    base_dir = None

    @classmethod
    def factory_boy_seed_random(cls, seed=1) -> None:
        """
        Seeds the shared random number generator to generate same data

        Args:
            seed (int): seed

        Returns:
            None
        """
        if seed is None:
            seed = 1
        factory.random.reseed_random(seed)
        Faker.seed(seed)
        UniqIdService.set_fake_generator(start_id=900)

    @classmethod
    def setup_class(cls):
        cls.clean_sandbox()
        cls.factory_boy_seed_random()

    def setup_method(self, method):
        pass

    @classmethod
    def teardown_class(cls):
        cls.empty_sandbox()

    @classmethod
    def set_base_dir(cls, base_dir):
        cls.base_dir = base_dir

    @classmethod
    def get_base_dir(cls):
        """Get base dir from django settings by default"""
        if cls.base_dir is None:
            from django.conf import settings

            cls.base_dir = str(settings.BASE_DIR)
        return cls.base_dir

    @classmethod
    def get_tmp_dir(cls):
        """Get tmp test directory"""
        return f"{cls.get_base_dir()}/.donotcommit_tmp"

    @classmethod
    def get_tmp_diff_cmd_filename(cls):
        return f"{cls.get_tmp_dir()}/.donotcommit_tmp_diff_cmd"

    @classmethod
    def get_test_fixtures_dir(cls) -> str:
        """
        Get fixtures directory

        Returns:
            str: fixtures directory
        """
        if not cls._fixture_dir:
            filename = cls._get_calling_filename()
            pos = filename.find("/tests")
            if not pos > 0:
                raise ValueError(f"Unable to determine root tests path from {filename}")
            cls._fixture_dir = f"{filename[:pos]}/tests/_fixtures"
            if not os.path.exists(cls._fixture_dir):
                cls._fixture_dir = f"{filename[:pos]}/tests/fixtures"

        return cls._fixture_dir

    @classmethod
    def get_resultsets_dir(cls) -> str:
        """
        Get result sets dir

        Returns:
            str: result sets directory
        """
        return f"{cls.get_test_fixtures_dir()}/resultsets"

    @classmethod
    def get_datasets_dir(cls, filename=None) -> str:
        """
        get data sets path

        Args:
            filename (str): related path of filename

        Returns:
            str: data sets directory
        """
        basedir = f"{cls.get_test_fixtures_dir()}/datasets"
        if filename:
            return f"{basedir}/{filename}"
        return basedir

    @classmethod
    def get_w_datasets_dir(cls, filename) -> str:
        """
        get w data sets path

        Args:
            filename (str): related path of filename

        Returns:
            str: common data sets directory
        """
        if not cls._w_fixture_dir:
            w_dir = os.path.dirname(os.path.realpath(__file__))
            pos = w_dir.find("/tests")
            if not pos > 0:
                raise ValueError("Unable to determine root common tests path")
            cls._w_fixture_dir = f"{w_dir[:pos]}/tests/fixtures"
        return f"{cls._w_fixture_dir}/datasets/{filename}"

    @classmethod
    def get_app_datasets_dir(cls, filename, app) -> str:
        from django.conf import settings

        root_dir = Path(settings.BASE_DIR).parent
        return f"{root_dir}/{app}/tests/fixtures/datasets/{filename}"

    @classmethod
    def _get_dataset(cls, dataset, dataset_filename):
        """
        Get fixture dataset
        Args:
            dataset(str): relative path to dataset.
                          If is json, load it else just read it

        Returns:
            mixed
        """
        filename, file_extension = os.path.splitext(dataset)
        with open(dataset_filename) as file:
            if file_extension == ".json":
                return json.load(file)
            return file.read()

    @classmethod
    def get_dataset(cls, dataset):
        """
        Get fixture dataset
        Args:
            dataset(str): relative path to dataset.
                          If is json, load it else just read it

        Returns:
            mixed
        """
        return cls._get_dataset(dataset, cls.get_datasets_dir(dataset))

    @classmethod
    def get_w_dataset(cls, dataset):
        """
        Get fixture from wedge dataset
        Args:
            dataset(str): relative path to dataset.
                          If is json, load it else just read it

        Returns:
            mixed
        """
        return cls._get_dataset(dataset, cls.get_w_datasets_dir(dataset))

    @classmethod
    def get_app_dataset(cls, dataset, app):
        """
        Get fixture from django app dataset
        Args:
           dataset(str): relative path to dataset.
                         If is json, load it else just read it
           app(str): django app

        Returns:
           mixed
        """
        return cls._get_dataset(dataset, cls.get_app_datasets_dir(dataset, app))

    @classmethod
    def _save_json_file_as_fixture(cls, fixture_filename, dataset):
        new_json = cls._convert_dataset_to_json(dataset)
        if fixture_filename.exists():
            actual = fixture_filename.read_text()
            if actual == new_json:
                return None
        else:
            cls._check_file_can_be_created(fixture_filename)
        fixture_filename.write_text(new_json)

    @classmethod
    def _save_bytes_file_as_fixture(cls, fixture_filename, dataset):
        if fixture_filename.exists():
            actual = fixture_filename.read_bytes()
            if actual == dataset:
                return None
        else:
            cls._check_file_can_be_created(fixture_filename)
        fixture_filename.write_bytes(dataset)

    @classmethod
    def _save_as_fixture(cls, fixture_filename, dataset):
        fixture_filename = Path(fixture_filename)

        if fixture_filename.suffix == ".json":
            cls._save_json_file_as_fixture(fixture_filename, dataset)
        else:
            cls._save_bytes_file_as_fixture(fixture_filename, dataset)

    @classmethod
    def _convert_dataset_to_json(cls, dataset):
        return (
            json.dumps(
                cls._convert_data(dataset),
                separators=(",", ": "),
                default=str,
                # disable non-ASCII characters escape with \uXXXX sequences
                ensure_ascii=False,
            )
            + "\n"
        )  # for respecting file empty last line convention

    @classmethod
    def save_as_dataset(cls, relative_filename, dataset):
        fixture_filename = cls.get_datasets_dir(relative_filename)
        cls._save_as_fixture(fixture_filename, dataset)

    @classmethod
    def get_sandbox_dir(cls, filename=None) -> str:
        """
        Get sandbox dir for current test

        Returns:
            str
        """
        sandbox_path = f"{cls._get_root_sandbox_dir()}/{cls.__name__}"
        if filename is None:
            return sandbox_path
        filename = f"{sandbox_path}/{filename}"
        FilesystemService.check_file_can_be_created(filename)
        return filename

    @classmethod
    def clean_sandbox(cls):
        """
        Clean sandbox
        """
        if not os.path.exists(cls.get_sandbox_dir()):
            os.makedirs(cls.get_sandbox_dir())
        FilesystemService.empty_dir(cls.get_sandbox_dir())

    @classmethod
    def empty_sandbox(cls):
        if not os.path.exists(cls._get_root_sandbox_dir()):
            os.makedirs(cls._get_root_sandbox_dir())
        FilesystemService.empty_dir(cls._get_root_sandbox_dir())

    @classmethod
    def get_mock_calls(cls, mock):
        """
        Get mock calls
        Args:
            mock(MagicMock|dict): mock or mock list

        Returns:
            list|dict
        """
        if isinstance(mock, dict):
            calls = {}
            for method, mock in mock.items():
                calls[method] = cls.get_mock_calls(mock)
            return calls

        calls = []
        if mock.call_count > 0:
            for call in mock.call_args_list:
                args, kwargs = call
                calls.append({"args": list(args), "kwargs": kwargs})
            return calls

        for call in mock.method_calls:
            method, args, kwargs = call
            calls.append({"method": method, "args": list(args), "kwargs": kwargs})

        return calls

    def assert_equals_resultset(self, actual, **kwargs):
        """
        assert result set equality

        Build resultset name from filename.
        Compare expected to resultset for tests method
        """

        # build resultset filename from caller filename
        calling_filename = kwargs.get("calling_filename", None)
        filename = self._get_calling_filename()
        calling_frame = self._get_calframe(calling_filename)
        method_name = self._get_calling_method_name(calling_frame)
        sub_dir = self._get_test_subdir(filename)
        filename_noext = path.basename(filename).replace(".py", "")
        resultset_filename = (
            f"{self.get_resultsets_dir()}/{sub_dir}/{filename_noext}/{method_name}.json"
        )
        self._check_file_can_be_created(resultset_filename)

        actual_json = (
            json.dumps(
                self._convert_data(actual),
                indent=4,
                separators=(",", ": "),
                default=str,
                # disable non-ASCII characters escape with \uXXXX sequences
                ensure_ascii=False,
            )
            + "\n"  # for respecting file empty last line convention
        )

        if os.path.exists(resultset_filename) is False:
            autosave_mode = os.environ.get("TEST_RESULTSET_AUTOSAVE", False)
            data = actual_json if autosave_mode else "{}"
            # create missing file
            with open(resultset_filename, "w") as f:
                f.write(data)

        # get expected result sets from file
        with open(resultset_filename) as json_file:
            expected = json_file.read()

        # assert
        try:
            assert expected == actual_json
        except AssertionError as e:
            working_dir = self.get_base_dir()
            tmp_dir = self.get_tmp_dir()

            # build fix result set
            tmp_actual_filename = (
                f"{tmp_dir}/{filename_noext}-{method_name}_ACTUAL.json"
            )
            self._check_file_can_be_created(tmp_actual_filename)

            with open(tmp_actual_filename, "w") as f:
                f.write(actual_json)

            default_diff_tool = os.getenv(
                "DEFAULT_TU_DIFF_TOOL", "charm diff __expected__ __actual__"
            )
            diff_cmd = default_diff_tool.replace(
                "__expected__", resultset_filename
            ).replace("__actual__", tmp_actual_filename)
            # noinspection StandardShellInjection
            os.system(diff_cmd)

            print(f"\n\033[1;31m=== TEST {method_name} has failed !!")
            print(f"file: {filename.replace(working_dir, '')}")
            os.system(f"diff {resultset_filename} {tmp_actual_filename}")
            print(f"=== TEST {method_name}\n\033[0m")
            raise e

    @classmethod
    def show_test_failed_diff(cls):
        """
        Show diff errors on failed tests
        Add this to your conftest.py for automatic call

            @pytest.fixture(scope="session", autouse=True)
            def show_diff_errors(request):
                request.addfinalizer(TestCaseMixin.show_diff)

        """
        filename = TestCaseMixin.get_tmp_diff_cmd_filename()
        if os.path.isfile(filename):
            with open(filename) as f:
                list_cmd = f.read()
            os.remove(filename)
            for cmd in list_cmd.split("\n"):
                os.system(cmd)  # noqa

    @staticmethod
    def assert_file_exists(filename):
        assert os.path.exists(filename), f"{filename} not found"

    @staticmethod
    def assert_file_not_exists(filename):
        assert not os.path.exists(filename), f"{filename} found"

    @staticmethod
    def assert_log(capture, expected_log: str):
        """
        Check the expected log is among the logs captured during the test.

        Args:
            capture: captured logs
            expected_log(str): log expected to be among the captured logs
        """
        assert any(
            capture_record.getMessage() == expected_log
            for capture_record in capture.records
        ), (
            f"\nExpected log:\n'{expected_log}'\ngot instead:\n"
            f"{'\n'.join([f"- '{r.getMessage()}'" for r in capture.records])}"
        )

    @classmethod
    def _get_test_subdir(cls, filename):
        """
        Get subdir after tests directory
        Args:
            filename:

        Returns:

        """
        working_dir = cls.get_base_dir()
        dir_names = path.dirname(filename.replace(working_dir, "")).split("/")

        # search tests dir
        for _ in range(0, len(dir_names)):
            dir_name = dir_names.pop(0)
            if dir_name == "tests":
                break

        return "/".join(dir_names)

    @classmethod
    def _get_root_sandbox_dir(cls):
        """
        Get root sandbox dir
        Returns:
            str: root sandbox directory
        """
        return f"{cls.get_test_fixtures_dir()}/sandbox"

    @classmethod
    def _get_calframe(cls, calling_filename=None) -> inspect.FrameInfo:
        """
        find calling frame from stack calls
        Returns:
            FrameInfo : frame
        """
        # find calling frame
        calframe = inspect.getouterframes(inspect.currentframe(), 2)
        test_filename = (
            cls._get_calling_filename() if not calling_filename else calling_filename
        )
        for frame in calframe:
            if frame.filename.find(test_filename) >= 0:
                return frame
        raise ValueError("Unable to determine calling frame")

    @classmethod
    def _get_calling_filename(cls) -> str:
        """
        Returns:
            str: calling filename
        """
        return inspect.getfile(cls)

    @staticmethod
    def _get_calling_method_name(frame) -> str:
        """
        Returns:
            str: calling method name
        """
        return frame[3]

    @staticmethod
    def _get_calling_lineno(frame) -> str:
        """
        Returns:
            str: calling line number
        """
        return frame.lineno

    @staticmethod
    def _check_file_can_be_created(filename) -> None:
        """
        create missing directories for filename
        Args:
            filename (str) : fullpath filename

        Returns:
            None
        """
        return FilesystemService.check_file_can_be_created(filename)

    @classmethod
    def _convert_data(cls, data):
        from w.services.technical.json_service import JsonService

        return JsonService.to_json_dumpable(data)

    @staticmethod
    def reset_sequence_builders(
        list_builders: List[Type[AbstractTestBuilder]], reset_pk_model=True
    ):
        # remove duplicate
        list_builders = list(dict.fromkeys(list_builders))
        for builder in list_builders:
            builder.reset_sequence(reset_pk_model=reset_pk_model)
