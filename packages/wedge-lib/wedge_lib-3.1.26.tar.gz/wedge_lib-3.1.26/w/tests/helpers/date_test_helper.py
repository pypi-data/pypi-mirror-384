from contextlib import contextmanager


from w.test_utils.helpers import date_test_helper


@contextmanager
def today_is(d):
    # deprecated
    with date_test_helper.today_is(d) as m:
        yield m
