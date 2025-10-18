import os

from w.services.abstract_service import AbstractService


class EnvService(AbstractService):
    SETTING_MISSING = "__settings_is_missing__"

    @classmethod
    def get_var_env(cls, name, default=None):
        """Get var env, if default is None => MUST BE DEFINED AS ENVIRONMENT VAR"""
        default = cls._missing_value(name) if default is None else default
        return os.getenv(name, default)

    @classmethod
    def get_var_env_list(cls, name, default=None):
        var = cls.get_var_env(name, default)
        if isinstance(var, str):
            return var if var.startswith(cls.SETTING_MISSING) else var.split(",")
        return var

    @classmethod
    def get_var_env_bool(cls, name, default=None):
        var = cls.get_var_env(name, default)
        if var == cls._missing_value(name):
            return var
        var = str(var).lower()
        return var in ("true", "on", "1")

    @classmethod
    def get_var_env_without_trailing_slash(cls, name, default=None):
        var_env = cls.get_var_env(name, default)
        if var_env[-1] == os.sep:
            var_env = var_env[:-1]
        return var_env

    @classmethod
    def _missing_value(cls, name):
        return cls.SETTING_MISSING + name
