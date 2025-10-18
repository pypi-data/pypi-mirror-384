import subprocess
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from w.exceptions import NotFoundError

from w.services.abstract_service import AbstractService
from w.services.technical.filesystem_service import FilesystemService

from w.services.technical.models.tpl_models import TplSettings


class TplService(AbstractService):
    tpl_name = None
    _admin_conn = None
    _tpl_conn = None
    _tpl_db_name = None

    @classmethod
    @contextmanager
    def session(cls, settings: TplSettings) -> Generator:
        if cls._is_initialized():
            raise RuntimeError("a session is already in progress")
        cls._settings = settings
        cls.tpl_name = settings.tpl_name
        cls._tpl_db_name = settings.tpl_db_name
        cls._tpl_conn_settings = {
            **settings.to_connection_dict(),
            "database": cls._tpl_db_name,
        }
        cls._admin_db_name = "template1"
        cls._admin_conn = cls._get_conn(
            {**settings.to_connection_dict(), "database": cls._admin_db_name}
        )
        try:
            yield
        finally:
            cls.clear()

    @classmethod
    def tpl_create(cls) -> None:
        cls._check_is_initialized()
        cls._run_sql(cls._admin_conn, cls._create_sql(cls._tpl_db_name))
        return None

    @classmethod
    def tpl_delete(cls) -> None:
        cls._check_is_initialized()
        if cls.is_tpl_db_exists():
            cls._run_sql(cls._admin_conn, cls._delete_sql(cls._tpl_db_name))
        return None

    @classmethod
    def tpl_recreate(cls) -> None:
        cls.tpl_delete()
        cls.tpl_create()
        return None

    @classmethod
    def target_delete(cls, target_db_name) -> None:
        cls._check_is_initialized()
        if cls._is_db_exists(target_db_name):
            cls._run_sql(cls._admin_conn, cls._delete_sql(target_db_name))
        return None

    @classmethod
    def is_tpl_db_exists(cls) -> bool:
        cls._check_is_initialized()
        return cls._is_db_exists(cls._tpl_db_name)

    @classmethod
    def dump(cls) -> None:
        cls._check_is_initialized()
        dump_filename = cls._dump_sql_filename()
        FilesystemService.create_missing(dump_filename)
        dump_filename.unlink(missing_ok=True)
        p = subprocess.run(
            f"PGPASSWORD={cls._settings.db_password} "
            f"pg_dump --column-inserts --no-comments "
            f"-U {cls._settings.db_user} "
            f"-h {cls._settings.db_host} "
            f"-p {cls._settings.db_port} "
            f"--file={dump_filename} {cls._tpl_db_name}",
            shell=True,
        )
        cls._check_process_run(p, "dump")
        return None

    @classmethod
    def load(cls, target_db_name: str) -> None:
        cls._check_is_initialized()
        cls.target_delete(target_db_name)
        if cls.is_tpl_db_exists() is False:
            raise NotFoundError(f"'{cls.tpl_name}' tpl does not exist")
        cls._run_sql(
            cls._admin_conn,
            cls._clone_db_sql(db_target=target_db_name, tpl_db_name=cls._tpl_db_name),
        )
        return None

    @classmethod
    def init_tpl_from_db(cls, src_db: str) -> None:
        """Init tpl from another db"""
        cls._check_is_initialized()
        if cls._is_db_exists(src_db) is False:
            raise RuntimeError(f"db {src_db} does not exist")
        if cls.is_tpl_db_exists() is True:  # pragma: no cover
            cls.tpl_delete()
        cls._run_sql(
            cls._admin_conn,
            cls._clone_db_sql(db_target=cls._tpl_db_name, tpl_db_name=src_db),
        )
        return None

    @classmethod
    def restore_dump(cls) -> None:
        cls._check_is_initialized()
        dump_filename = cls._dump_sql_filename()
        if dump_filename.exists() is False:
            raise RuntimeError(f"no dump sql found for tpl {cls.tpl_name}")
        with dump_filename.open() as f:
            sql = f.read()

        cls.tpl_recreate()
        conn = cls._get_tpl_conn()
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"restore failed: {e}")
        finally:
            cls._close_conn(conn)
        return None

    @classmethod
    def clear(cls) -> None:
        if cls._admin_conn:
            cls._admin_conn.close()
            cls._admin_conn = None
        return None

    @classmethod
    def _get_tpl_conn(cls):
        return cls._get_conn(cls._tpl_conn_settings)

    @classmethod
    def _get_conn(cls, conn_settings: dict):
        try:
            _conn = psycopg2.connect(**conn_settings)
            _conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        except psycopg2.OperationalError:  # pragma: no cover
            return None
        return _conn

    @classmethod
    def _close_conn(cls, conn) -> None:
        if conn:
            conn.close()
        return None

    @classmethod
    def _is_db_exists(cls, db_name: str) -> bool:
        result = cls._fetch_sql(cls._admin_conn, cls._is_db_exists_sql(db_name))
        return len(result) == 1 and result[0][0] == db_name

    @classmethod
    def _is_db_exists_sql(cls, db_name: str) -> str:
        return (
            "SELECT datname FROM pg_catalog.pg_database "
            f"WHERE lower(datname) = lower('{db_name}');"
        )

    @classmethod
    def _create_sql(cls, db_name: str) -> str:
        return f"CREATE DATABASE {db_name}"

    @classmethod
    def _delete_sql(cls, db_name: str) -> str:
        return f"DROP DATABASE IF EXISTS {db_name}"

    @classmethod
    def _clone_db_sql(cls, db_target: str, tpl_db_name: str) -> str:
        return f"CREATE DATABASE {db_target} TEMPLATE {tpl_db_name};"

    @classmethod
    def _run_sql(cls, conn, sql: str) -> None:
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
        except Exception as e:  # pragma: no cover
            raise RuntimeError(f"sql execution failed: {e}")
        return None

    @classmethod
    def _fetch_sql(cls, conn, sql: str) -> Any:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            return cursor.fetchall()

    @classmethod
    def _is_initialized(cls) -> bool:
        return cls._admin_conn is not None

    @classmethod
    def _dump_sql_filename(cls) -> Path:
        return cls._settings.full_dump_sql_filename

    @staticmethod
    def _check_process_run(p: Any, action: str) -> None:
        if p.returncode != 0:  # pragma: no cover
            raise RuntimeError(f"{action} has failed")
        return None
