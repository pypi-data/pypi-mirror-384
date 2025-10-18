from contextlib import contextmanager
from django.db import connection
from django.test.utils import CaptureQueriesContext


@contextmanager
def capture_nb_queries(expected):
    """capture sql queries and assert expected number"""
    with CaptureQueriesContext(connection):
        yield connection
    actual = len(connection.queries)
    assert actual == expected, f"nb captured queries {actual} != {expected} expected"
