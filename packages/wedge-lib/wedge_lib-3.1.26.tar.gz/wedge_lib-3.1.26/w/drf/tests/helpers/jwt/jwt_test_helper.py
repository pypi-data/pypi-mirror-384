from contextlib import contextmanager
from dataclasses import dataclass
from unittest.mock import patch

from w.tests.helpers import date_test_helper


@dataclass
class FakeRefreshToken:
    access_token: str
    refresh_token: str

    def __str__(self) -> str:
        return self.refresh_token


@contextmanager
def with_refresh_token(
    access_token="mock-access-token", refresh_token="mock-refresh-token"
):
    target = "rest_framework_simplejwt.serializers.TokenObtainPairSerializer.get_token"
    token = FakeRefreshToken(access_token, refresh_token)
    with date_test_helper.today_is("2020-01-01 11:11:11"):
        with patch(target, return_value=token) as m:
            yield m
