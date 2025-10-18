from contextlib import contextmanager
from unittest.mock import patch

from w.pydantics.date_models import DateTime, Date, DateTimeIn


@contextmanager
def today_is(d: DateTimeIn | Date | DateTime):
    if isinstance(d, DateTimeIn):
        d = DateTime(d)

    with patch("django.utils.timezone.now", return_value=d.to_datetime()):
        with patch("arrow.utcnow", return_value=d._root_to_arrow()) as m:
            yield m
