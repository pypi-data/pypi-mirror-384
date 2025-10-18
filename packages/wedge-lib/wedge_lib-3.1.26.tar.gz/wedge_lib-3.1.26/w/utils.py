import datetime
import errno
import os
from decimal import Decimal
from importlib import import_module

from arrow import Arrow

from w.services.technical.dict_service import DictService
from w.services.technical.string_service import StringService


def import_path(path_module):
    """
    Dynamically import module

    Args:
        path_module(str): module path with . (ex: 'dir.dir2.file.Class')

    Returns:
        module
    """
    package, attr = path_module.rsplit(".", 1)
    return getattr(import_module(package), attr)


def dict_keep_keys(d, keys):
    """
    Remove key not in keys from dictionary

    Args:
        d(dict): dictionary to clean
        keys(list): dictionary keys to keep

    Returns:
        dict: cleaned dictionary
    """
    return DictService.keep_keys(d, keys)


def dict_remove_keys(d, keys):
    """
    Remove key in keys from dictionary

    Args:
        d(dict): dictionary to clean
        keys(list): dictionary keys to remove

    Returns:
        dict: cleaned dictionary
    """
    return DictService.remove_keys(d, keys)


def get_dict_last_values(d):
    """
    get last entry value
    Args:
        d(dict): dictonnary

    Returns:
        mixed
    """
    return DictService.get_last_entry_value(d)


def to_json_dumpable(data):
    """
    Convert data to be json dumpable
    """
    if isinstance(data, tuple):
        data = list(data)

    if isinstance(data, dict):
        for k, v in data.items():
            data[k] = to_json_dumpable(v)
        return data

    if isinstance(data, list):
        for i in data:
            to_json_dumpable(i)
        return data

    if isinstance(data, Decimal):
        return float(data)

    if isinstance(data, Arrow):
        return data.format()

    elif isinstance(data, datetime.datetime) or isinstance(data, datetime.date):
        return data.strftime("%Y-%m-%d %H:%M:%S")

    return data


def check_file_can_be_created(filename) -> None:
    """
    create missing directories for filename

    Args:
        filename (str) : fullpath filename

    Returns:
        None
    """
    if not os.path.exists(filename):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise


def round_of_rating(number):
    """
    Round a number to the closest half integer.

    Args:
        number:

    Returns:
        >>> round_of_rating(1.3)
        1.5
        >>> round_of_rating(2.6)
        2.5
        >>> round_of_rating(3.0)
        3.0
        >>> round_of_rating(4.1)
        4.0
    """

    return round(number * 2) / 2


def strip_accents(txt):
    """Remove string accents"""
    return StringService.strip_accents(txt)
