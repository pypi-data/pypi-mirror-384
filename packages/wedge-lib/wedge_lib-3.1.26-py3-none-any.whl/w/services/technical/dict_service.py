import copy

from w.services.abstract_service import AbstractService
from mergedeep import merge


class DictService(AbstractService):
    @classmethod
    def keep_keys(cls, d: dict, keys: list):
        """
        Remove key not in keys from dictionary

        Args:
            d(dict): dictionary to clean
            keys(list): dictionary keys to keep

        Returns:
            dict: cleaned dictionary
        """
        return {k: v for k, v in d.items() if k in keys}

    @classmethod
    def remove_keys(cls, d: dict, keys: list):
        """
        Remove key in keys from dictionary

        Args:
            d(dict): dictionary to clean
            keys(list): dictionary keys to remove

        Returns:
            dict: cleaned dictionary
        """
        return {k: v for k, v in d.items() if k not in keys}

    @classmethod
    def get_last_entry_value(cls, d: dict):
        """
        get last entry value

        Args:
            d(dict): dictonnary

        Returns:
            mixed
        """
        return d[list(d.keys())[-1]]

    @classmethod
    def remap_keys(cls, d: dict, remap_keys: dict) -> dict:
        """remap a dictionnary keys and keep only key found in remap_keys"""
        remaped = {}
        for old, new in remap_keys.items():
            remaped[new] = d[old]
        return remaped

    @classmethod
    def deep_merge(cls, dict1, dict2):
        """Merge deeply dict2 with dict1"""
        return merge(copy.deepcopy(dict1), dict2)
