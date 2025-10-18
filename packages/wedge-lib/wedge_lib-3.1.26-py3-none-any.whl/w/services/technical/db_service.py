from w.services.abstract_service import AbstractService
from django.db import connection


class DbService(AbstractService):
    @staticmethod
    def exec_sql(sql, params=None):
        if params is None:
            params = []
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            columns = [col[0] for col in cursor.description]
            result = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return result
