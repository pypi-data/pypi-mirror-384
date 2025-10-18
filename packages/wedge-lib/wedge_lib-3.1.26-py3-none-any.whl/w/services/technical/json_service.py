import datetime
import json
from decimal import Decimal

from pydantic import BaseModel

from w.services.abstract_service import AbstractService
from w.services.technical.filesystem_service import FilesystemService


class JsonService(AbstractService):
    @classmethod
    def dump_to_file(cls, data, filename, human_readable=False):
        """
        Dump json into file
        """
        default_args = {"obj": data}
        human_readable_args = {
            "indent": 4,
            "separators": (",", ": "),
            "default": str,
            # disable non-ASCII characters escape with \uXXXX sequences
            "ensure_ascii": False,
        }
        with open(filename, "w") as f:
            args = {**default_args, **{"fp": f}}
            if human_readable:
                args = {**args, **human_readable_args}
            json.dump(**args)

    @classmethod
    def to_json_dumpable(cls, data):
        """
        Convert data to be json dumpable
        """
        from w.services.technical.date_service import DateService

        if isinstance(data, Decimal):
            return float(data)

        if isinstance(data, datetime.datetime):
            return DateService.to_mysql_datetime(data)

        if isinstance(data, datetime.date):
            return DateService.to_mysql_date(data)

        if isinstance(data, dict):
            for k, v in data.items():
                data[k] = cls.to_json_dumpable(v)
            return data

        if isinstance(data, list):
            for idx, i in enumerate(data):
                data[idx] = cls.to_json_dumpable(i)
            return data

        if isinstance(data, BaseModel):
            return data.model_dump()

        if isinstance(data, tuple):
            data = cls.to_json_dumpable(list(data))

        if isinstance(data, set):
            data = cls.to_json_dumpable(list(data))

        if isinstance(data, bytes):
            return data.decode("utf-8")

        return data

    @staticmethod
    def load_from_file(filename):
        """
        Load json from file

        Args:
            filename(str):

        Returns:
            Any
        """
        FilesystemService.check_file_exists(filename)
        with open(filename) as f:
            return json.load(f)

    @staticmethod
    def load_from_str(str_json: str):
        """
        Load json from str

        Args:
            str_json(str):

        Returns:
            Any
        """
        return json.loads(str_json)

    @staticmethod
    def is_valid(json_data) -> bool:
        """
        Check json is valid

        Args:
            json_data(str): json to check

        Returns:
            bool
        """
        try:
            json.loads(json_data)
            return True
        except ValueError:
            return False

    @classmethod
    def dump(cls, data) -> str:
        """
        Dump data into json string, convert data to be dumpable

        Args:
            data(mixed): python data

        Returns:
            str: json
        """
        return json.dumps(JsonService.to_json_dumpable(data))
