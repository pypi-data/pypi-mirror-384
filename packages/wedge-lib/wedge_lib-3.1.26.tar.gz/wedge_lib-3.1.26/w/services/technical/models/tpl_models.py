from pathlib import Path
from typing import Any

from django.conf import settings
from pydantic import BaseModel, Field, field_validator, model_validator


class TplSettings(BaseModel):
    tpl_name: str
    app: str
    db_user: str = Field(alias="USER")
    db_password: str = Field(alias="PASSWORD")
    db_host: str = Field(alias="HOST")
    db_port: int = Field(alias="PORT")
    prefix_tpl_db: str

    @field_validator("prefix_tpl_db", mode="before")
    @classmethod
    def check_prefix_tpl_db(cls, value: str) -> str:
        if value and value != "__TPL_DB_PREFIX_settings_missing__":
            return value

        raise ValueError("value or TPL_DB_PREFIX Django settings is missing")

    @model_validator(mode="before")
    @classmethod
    def set_default_prefix_tpl_db(cls, data: Any) -> Any:
        if (
            not data.get("prefix_tpl_db")
            and hasattr(settings, "TPL_DB_PREFIX")
            and settings.TPL_DB_PREFIX
        ):
            data["prefix_tpl_db"] = settings.TPL_DB_PREFIX
        else:
            data["prefix_tpl_db"] = "__TPL_DB_PREFIX_settings_missing__"

        return data

    def to_connection_dict(self) -> dict:
        return {
            "database": self.tpl_db_name,
            "user": self.db_user,
            "password": self.db_password,
            "host": self.db_host,
            "port": self.db_port,
        }

    @property
    def tpl_db_name(self) -> str:
        return f"{self.prefix_tpl_db}{self.tpl_name}"

    @property
    def dump_sql_filename(self) -> str:
        return f"{self.tpl_name}.sql"

    @property
    def tpl_dump_path(self) -> Path:
        return Path(settings.ROOT_DIR).joinpath(self.relative_tpl_dump_path)

    @property
    def full_dump_sql_filename(self) -> Path:
        return Path(f"{self.tpl_dump_path}/{self.dump_sql_filename}")

    @property
    def relative_tpl_dump_path(self) -> Path:
        relative_path = Path(self.app, "tests", "tpl_dumps")
        return relative_path

    @property
    def relative_dump_sql_filename(self) -> Path:
        return Path(self.relative_tpl_dump_path, self.dump_sql_filename)
