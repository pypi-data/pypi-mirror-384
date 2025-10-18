from io import StringIO

import yaml

from w.services.abstract_service import AbstractService
from w.services.technical.filesystem_service import FilesystemService


class YamlService(AbstractService):
    @staticmethod
    def dump_to_mem_file(data):
        """
        Convert a Yaml python object to in-memory yaml file
        """
        return StringIO(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))

    @staticmethod
    def dump_to_file(data, filename):
        """
        Dump data to filename
        """
        with open(filename, "w") as f:
            yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)

    @staticmethod
    def load_from_file(filename):
        """
        Parse the YAML document from filename
        and produce the corresponding Python object.

        Args:
            filename(str):

        Returns:
            dict
        """
        FilesystemService.check_file_exists(filename)
        with open(filename) as f:
            return yaml.safe_load(f)

    @classmethod
    def check_is_valid(cls, yaml_stream):
        """
        Check is valid Yaml
        Args:
            yaml_stream():

        Returns:
            Dict: Yaml converted to dict

        Raises:
            RuntimeError
        """
        is_valid, result = cls.is_valid(yaml_stream)
        if is_valid:
            return result
        raise RuntimeError(result["user_message"])

    @staticmethod
    def is_valid(yaml_stream):
        """
        Check yaml is valid
        Args:
            yaml_stream:

        Returns:
            (Bool, result): yaml is valid ?,
                if is valid result = Yaml converted to dict
                else result = error as :
                {
                    "line": <line>,
                    "col": <col>,
                    "error": <error message>,
                    "user_message": <displayable message>
                }
        """
        try:
            return True, yaml.safe_load(yaml_stream)
        except yaml.YAMLError as e:
            # noinspection PyUnresolvedReferences
            err = {
                "line": e.problem_mark.line + 1,
                "col": e.problem_mark.column + 1,
                "error": e.problem,
                "user_message": (
                    f"Line {e.problem_mark.line + 1}, "
                    f"column {e.problem_mark.column + 1}: {e.problem}"
                ),
            }
            return False, err
        except ValueError as e:
            err = {"user_message": f"Date format error in rulebook: {e}"}
            return False, err
