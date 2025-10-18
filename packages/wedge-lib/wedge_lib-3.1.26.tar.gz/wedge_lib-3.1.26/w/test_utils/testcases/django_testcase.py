from django.contrib.auth.models import Permission
from django.db import connection
from django.test import RequestFactory, TestCase

from w.django import utils
from w.tests.mixins.testcase_mixin import TestCaseMixin


class DjangoTestCase(TestCaseMixin, TestCase):
    """For testing in Django Context"""

    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.reset_all_db_sequences()
        cls.factory_boy_seed_random()

    @classmethod
    def setup_class(cls):
        # ignore TestCaseMixin.setup_class because it is already called in setUpTestData
        pass

    @classmethod
    def reset_all_db_sequences(cls):
        if connection.vendor != "postgresql":
            return None

        sql = """
        SELECT seqclass.relname     AS sequence_name,
               depclass.relname     AS table_name
        FROM   pg_class AS seqclass
               JOIN pg_sequence AS seq
                 ON ( seq.seqrelid = seqclass.relfilenode )
               JOIN pg_depend AS dep
                 ON ( seq.seqrelid = dep.objid )
               JOIN pg_class AS depclass
                 ON ( dep.refobjid = depclass.relfilenode )
        WHERE seqclass.relkind = 'S'
        """
        with connection.cursor() as c:
            c.execute(sql)
            results = c.fetchall()

            for sequence in results:
                sql = f"SELECT MAX(id) FROM {sequence[1]}"
                c.execute(sql)
                max_id = c.fetchall()[0][0]
                if max_id is None:
                    max_id = 0
                sql = f"ALTER SEQUENCE {sequence[0]} RESTART {max_id + 1};"
                c.execute(sql)

    @staticmethod
    def get_request(url, data=None, method="get", **extra):
        request = RequestFactory()

        if method == "get":
            return request.get(url, data, **extra)
        return request.post(url, data, **extra)

    @staticmethod
    def add_user_permission(user, permission):
        """
        Add permission to user
        """
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.add(permission)

    @staticmethod
    def reverse(url_name, params=None, query_params=None):
        """ "
        Url reverse with query string management

        Usage:
            self.reverse(
                'app.views.my_view',
                params={'pk': 123},
                query_kwargs={'key':'value', 'k2': 'v2'}
            )
        """
        return utils.reverse(
            viewname=url_name, kwargs=params, query_kwargs=query_params
        )
