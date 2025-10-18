import datetime

import pytest
from pydantic import BaseModel, ValidationError

from w.pydantics.date_models import DateTime, Date
from w.test_utils.helpers import date_test_helper
from w.test_utils.testcases.vo_testcase import VoTestCase


class PydanticModelWithDateTime(BaseModel):
    une_datetemps: DateTime


class PydanticModelWithDate(BaseModel):
    une_date: Date


class TestDateTime(VoTestCase):
    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.datetime = DateTime("2019-10-31T09:12:45.123456")
        cls.datetime_greater = DateTime("2019-10-31T09:12:45.123457")
        cls.datetime_same = DateTime("2019-10-31T09:12:45.123456")

    """
    init
    """

    def test_init_with_invalid_date_raise_value_error(self):
        with pytest.raises(ValueError):
            DateTime("invalid_date")

    """
    now
    """

    def test_now_with_success(self):
        with date_test_helper.today_is("2019-10-31 09:12:45.123456"):
            actual = DateTime.now()
            assert isinstance(actual, DateTime)
        assert str(actual) == "2019-10-31T09:12:45.123456+00:00"

    """
    parse
    """

    def test_parse_with_invalid_date_raise_value_error(self):
        match = "Failed to match 'D/M/YYYY HH:mm:ss' when parsing 'invalid_date'."
        with pytest.raises(ValueError, match=match):
            DateTime.parse("invalid_date", "D/M/YYYY HH:mm:ss")

    def test_parse_with_success_return_datetime(self):
        actual = DateTime.parse("31/10/2019 09:12:45", "D/M/YYYY HH:mm:ss")
        assert isinstance(actual, DateTime)
        assert str(actual) == "2019-10-31T09:12:45+00:00"

    """
    comparing
    """

    def test_comparing_with_failure(self):
        self.assert_comparing_failed(
            self.datetime, self.datetime_greater, self.datetime_same
        )

    def test_comparing_with_success(self):
        self.assert_comparing_succeed(
            self.datetime, self.datetime_greater, self.datetime_same
        )

    """
    substract
    """

    def test_substract_with_success(self):
        date1 = DateTime("2019-10-31 09:12:45.123456")
        date2 = DateTime("2019-10-30 09:00:00.0000")
        assert str(date1 - date2) == "1 day, 0:12:45.123456"
        assert str(date2 - date1) == "-2 days, 23:47:14.876544"

    """
    copy
    """

    def test_copy_with_success(self):
        self.assert_copy(self.datetime)

    """
    to_mysql_date
    """

    def test_to_mysql_date_with_success_return_str(self):
        expected = "2019-10-31"
        assert expected == self.datetime.to_mysql_date()

    """
    to_mysql_datetime
    """

    def test_to_mysql_datetime_with_success_return_str(self):
        expected = "2019-10-31 09:12:45.123456"
        assert expected == self.datetime.to_mysql_datetime()

    """
    to_date
    """

    def test_to_date_with_success_return_date(self):
        expected = datetime.date(2019, 10, 31)
        assert expected == self.datetime.to_date()

    """
    to_datetime
    """

    def test_to_datetime_with_success_return_datetime(self):
        expected = datetime.datetime(2019, 10, 31, 9, 12, 45, 123456)
        expected = expected.replace(tzinfo=datetime.timezone.utc)
        assert expected == self.datetime.to_datetime()

    """
    to_timestamp
    """

    def test_to_timestamps_with_success_return_float(self):
        expected = 1572513165.123456
        assert expected == self.datetime.to_timestamp()

    """
    to_timezone
    """

    def test_to_timezone_with_success_return_datetime(self):
        date = DateTime("2019-10-31 09:12:45.123456")
        ny_date = date.to_timezone("America/New_York")
        assert str(ny_date) == "2019-10-31T05:12:45.123456-04:00"

    """
    year
    """

    def test_year_with_success_return_int(self):
        date = DateTime("2019-10-31 09:12:45.123456")
        assert 2019 == date.year

    """
    format
    """

    def test_format_with_success_return_str(self):
        expected = "20191031"
        assert expected == self.datetime.format("YYYYMMDD")

    """
    shift
    """

    def test_shift_day(self):
        d = DateTime("2019-10-31 09:12:45")
        expected = DateTime("2019-10-31 11:13:45")
        assert expected == d.shift({"minutes": 1, "hours": 2})

    """
    reset_microseconds
    """

    def test_reset_microseconds_with_success(self):
        d = DateTime("2019-10-31 09:12:45.123456")
        actual = d.reset_microseconds()
        assert str(actual) == "2019-10-31T09:12:45+00:00"

    """
    model_json_schema
    """

    def test_schema_with_datetime_return_json(self):
        actual = PydanticModelWithDateTime.model_json_schema()
        self.assert_equals_resultset(actual)

    """
    pydantic
    """

    def test_pydantic_with_invalid_datetime_raise_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PydanticModelWithDateTime(une_datetemps="invalid-date")
        actual = exc_info.value.errors(include_url=False)
        self.assert_equals_resultset(actual)

    def test_pydantic_with_datetime_success(self):
        actual = PydanticModelWithDateTime(une_datetemps=self.datetime)
        assert actual.une_datetemps == self.datetime
        actual = PydanticModelWithDateTime(une_datetemps="2019-10-31 09:12:45.123456")
        self.assert_equals_resultset(actual)


class TestDate(VoTestCase):
    @classmethod
    def setup_class(cls):
        super().setup_class()
        cls.date = Date("2019-10-31T09:12:45.123456")
        cls.date_greater = Date("2019-11-01T09:12:45.123456")
        # only microseconds are !=
        cls.date_same = Date("2019-10-31T09:12:45.123457")

    """
    init
    """

    def test_init_with_invalid_date_raise_value_error(self):
        with pytest.raises(ValueError):
            Date("invalid_date")

    """
    now
    """

    def test_now_with_success(self):
        with date_test_helper.today_is("2019-10-31 09:12:45.123456"):
            actual = Date.now()
            assert isinstance(actual, Date)
        assert str(actual) == "2019-10-31T00:00:00+00:00"

    """
    parse
    """

    def test_parse_with_invalid_date_raise_value_error(self):
        match = "Failed to match 'D/M/YYYY' when parsing 'invalid_date'."
        with pytest.raises(ValueError, match=match):
            Date.parse("invalid_date", "D/M/YYYY")

    def test_parse_with_success_return_datetime(self):
        actual = Date.parse("31/10/2019", "D/M/YYYY")
        assert isinstance(actual, Date)
        assert str(actual) == "2019-10-31T00:00:00+00:00"

    """
    comparing
    """

    def test_comparing_with_failure(self):
        self.assert_comparing_failed(self.date, self.date_greater, self.date_same)

    def test_comparing_with_success(self):
        self.assert_comparing_succeed(self.date, self.date_greater, self.date_same)

    """
    substract
    """

    def test_substract_with_success(self):
        date1 = Date("2019-10-31")
        date2 = Date("2019-10-30")
        assert str(date1 - date2) == "1 day, 0:00:00"
        assert str(date2 - date1) == "-1 day, 0:00:00"

    """
    copy
    """

    def test_copy_with_success(self):
        self.assert_copy(self.date)

    """
    to_mysql_date
    """

    def test_to_mysql_date_with_success_return_str(self):
        expected = "2019-10-31"
        assert expected == self.date.to_mysql_date()

    """
    to_mysql_datetime
    """

    def test_to_mysql_datetime_with_success_return_str(self):
        expected = "2019-10-31 00:00:00.000000"
        assert expected == self.date.to_mysql_datetime()

    """
    to_date
    """

    def test_to_date_with_success_return_date(self):
        expected = datetime.date(2019, 10, 31)
        assert expected == self.date.to_date()

    """
    to_datetime
    """

    def test_to_datetime_with_success_return_datetime(self):
        expected = datetime.datetime(2019, 10, 31)
        expected = expected.replace(tzinfo=datetime.timezone.utc)
        assert expected == self.date.to_datetime()

    """
    to_timestamp
    """

    def test_to_timestamps_with_success_return_float(self):
        expected = 1572480000.0
        assert expected == self.date.to_timestamp()

    """
    format
    """

    def test_format_with_success_return_str(self):
        expected = "20191031"
        assert expected == self.date.format("YYYYMMDD")

    """
    shift
    """

    def test_shift_day(self):
        d = Date("2019-10-31")
        expected = Date("2019-11-01")
        assert expected == d.shift({"days": 1})

    """
    model_json_schema
    """

    def test_schema_with_date_return_json(self):
        actual = PydanticModelWithDate.model_json_schema()
        self.assert_equals_resultset(actual)

    """
    pydantic
    """

    def test_pydantic_with_invalid_date_raise_validation_error(self):
        with pytest.raises(ValidationError) as exc_info:
            PydanticModelWithDate(une_date="2018-09-GF")
        actual = exc_info.value.errors(include_url=False)
        self.assert_equals_resultset(actual)

    def test_pydantic_with_date_success(self):
        actual = PydanticModelWithDate(une_date=self.date)
        assert actual.une_date == self.date
        actual = PydanticModelWithDate(une_date="2019-10-31 09:12:45.123456")
        self.assert_equals_resultset(actual)
