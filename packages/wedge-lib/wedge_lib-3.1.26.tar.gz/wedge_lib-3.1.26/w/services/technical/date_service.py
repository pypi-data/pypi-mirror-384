import copy
import datetime

import arrow
from arrow import Arrow
from dateutil.relativedelta import relativedelta

from w.services.abstract_service import AbstractService


class DateService(AbstractService):
    """Service Date"""

    # day number
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4
    SAT = 5
    SUN = 6

    # timezone if none
    _timezone = None
    _locale = "en-us"

    @classmethod
    def clear(cls):
        super().clear()
        cls._timezone = None
        cls._locale = "en-us"

    @classmethod
    def set_timezone(cls, timezone):
        """
        Define default timezone

        Args:
            timezone(str):
        """
        cls._timezone = timezone

    @classmethod
    def set_locale(cls, locale: str = ""):
        cls._locale = locale

    @staticmethod
    def get(d) -> Arrow:
        """
        Get Arrow date from d
        Args:
            d(str|datetime.datetime|datetime.date)

        Returns:
            Arrow
        """
        return arrow.get(d)

    @staticmethod
    def now() -> Arrow:
        """
        Get now date
        Returns:
            Arrow
        """
        return arrow.utcnow()

    @classmethod
    def previous_weekday(cls, d, seeking_day) -> Arrow:
        """
        Determine the first previous weekday from a date

        Args:
            d (str|Arrow|datetime.datetime|datetime.date): arrow date to search from
            seeking_day (int):  seeking day num (use Date.MON, Date.TUE ...)

        Returns:
            Arrow: date to previous seeking day
        """
        d = cls._get(d, default_now=False)
        current_day = d.weekday()
        previous_date = copy.copy(d)

        if current_day == seeking_day:
            return d
        if current_day > seeking_day:
            nb_day = seeking_day - current_day
        else:
            nb_day = seeking_day - current_day - 7

        return previous_date.shift(days=nb_day)

    @classmethod
    def previous_month(cls, d=None) -> Arrow:  # pragma: no cover (todo one day)
        """
        Determine the previous weekday from a date

        Args:
            d(None|str|Arrow|datetime.datetime|datetime.date): today if not set

        Returns:
            Arrow: Last day of previous month
        """
        return cls._get(d).replace(day=1).shift(days=-1)

    @classmethod
    def next_weekday(cls, d, seeking_day) -> Arrow:
        """
        Determine the first next weekday from a date

        Args:
            d (str|Arrow|datetime.datetime|datetime.date): arrow date to search from
            seeking_day (int):  seeking day (use DateService.MON, DateService.TUE ...)

        Returns:
            Arrow: date to previous seeking day
        """
        d = cls._get(d, default_now=False)
        current_day = d.weekday()
        next_date = copy.copy(d)

        if current_day == seeking_day:
            return d
        if current_day < seeking_day:
            nb_day = seeking_day - current_day
        else:
            nb_day = seeking_day - current_day + 7

        return next_date.shift(days=nb_day)

    @classmethod
    def get_weekday_date(cls, d, seeking_day) -> Arrow:
        """
        Determine seeking_day date from a date in same week

        Args:
            d(str|Arrow|datetime.datetime|datetime.date): date to search from
            seeking_day (int):  seeking day (use DateService.MON, DateService.TUE ...)

        Returns:
            Arrow: date of seeking day
        """

        d = cls._get(d, default_now=False)

        current_day = d.weekday()
        if current_day == seeking_day:
            return d

        return d.shift(days=(seeking_day - current_day))

    @classmethod
    def to_mysql_date(cls, d=None) -> str:
        """
        Format date to mysql format string

        Args:
            d(None|str|Arrow|datetime.datetime|datetime.date): today if not set

        Returns:
            str: mysql date
        """
        return cls._format(d, "YYYY-MM-DD")

    @classmethod
    def to_mysql_datetime(cls, d=None) -> str:
        """
        Format datetime to mysql format string

        Args:
            d(None|str|Arrow|datetime.datetime|datetime.date): today if not set

        Returns:
            str: mysql date
        """
        return cls._format(d, "YYYY-MM-DD HH:mm:ss.SSSSSS")

    @classmethod
    def to_str(cls, date_format, d=None) -> str:
        """
        Format date to str to a format string

        Args:
            date_format(string): format string
            d(None|str|Arrow|datetime.datetime|datetime.date): today if not set

        Returns:
            str: mysql date
        """
        return cls._format(d, date_format)

    @staticmethod
    def week_number(d=None) -> int:
        """
        Get week number from date

        Args:
            d(Arrow|datetime.datetime|datetime.date):

        Returns:
            int
        """
        if d is None:
            d = datetime.datetime.today()
        elif isinstance(d, Arrow):
            d = d.datetime

        return d.isocalendar()[1]

    @classmethod
    def to_date(cls, d=None) -> datetime.date:
        """
        Convert date to datetime.date

        Args:
            d(None|str|Arrow): today if not set

        Returns:

        """
        return cls._get(d).date()

    @classmethod
    def to_datetime(cls, d=None) -> datetime.datetime:
        """
        Convert date to datetime.datetime.

        Args:
            d(None|str|Arrow): today if not set

        Returns:

        """
        d = cls._get(d)
        if cls._timezone:
            return d.to(cls._timezone).datetime
        return d.naive

    @classmethod
    def is_between(cls, d, start, end) -> bool:
        """
        Check if date is between start and end
        Args:
            d(str|Arrow|datetime.datetime|datetime.date): date to check
            start(str|Arrow|datetime.datetime|datetime.date): start date
            end(str|Arrow|datetime.datetime|datetime.date): end date

        Returns:
            bool
        """
        d = cls._get(d, default_now=False)
        start = cls._get(start)
        end = cls._get(end)

        cls._check_date_start_before_end(start, end)

        return start <= d <= end

    @classmethod
    def range_day(cls, start, end, **kwargs):
        """
        Returns an iterator of :class:`Arrow <arrow.arrow.Arrow>` objects, representing
        points in time between two inputs.

        Args:
            start(str|Arrow|datetime.datetime|datetime.date): start date
            end(str|Arrow|datetime.datetime|datetime.date): end date
            **kwargs: only_week_end : retrieve only weekend day (default False)

        Returns:
            list(Arrow)
        """
        exclude = []

        if kwargs.pop("only_week_end", False):
            exclude = range(cls.MON, cls.SAT)

        start, end = cls._get_start_end_and_validate_date(start, end)

        result = []
        for d in arrow.Arrow.range("day", start, end):
            if d.weekday() not in exclude:
                result.append(d)
        return result

    @classmethod
    def range_month(cls, start, end):
        """
        Returns an iterator of :class:`Arrow <arrow.arrow.Arrow>` objects, representing
        points in time between two inputs.

        Args:
            start(str|Arrow|datetime.datetime|datetime.date): start date
            end(str|Arrow|datetime.datetime|datetime.date): end date

        Returns:
            list(Arrow)
        """
        start, end = cls._get_start_end_and_validate_date(start, end)
        return arrow.Arrow.range("month", start, end)

    @classmethod
    def range_year(cls, start, end):
        """
        Returns an iterator of :class:`Arrow <arrow.arrow.Arrow>` objects, representing
        points in time between two inputs.

        Args:
            start(str|Arrow|datetime.datetime|datetime.date): start date
            end(str|Arrow|datetime.datetime|datetime.date): end date

        Returns:
            list(Arrow)
        """
        start, end = cls._get_start_end_and_validate_date(start, end)
        return arrow.Arrow.range("year", start, end)

    @classmethod
    def is_week_end(cls, d=None) -> bool:
        """
        Check is date is week end

        Args:
           d(str|Arrow|datetime.datetime|datetime.date): date to check, default today

        Returns:
            bool
        """
        d = cls._get(d)
        return d.weekday() in [DateService.SAT, DateService.SUN]

    @classmethod
    def add_days(cls, d, nb, exclude_we=False) -> Arrow:
        """
        Retrieve date by adding nb days. Optionally ignore week ends
        Args:
            d(str|Arrow|datetime.datetime|datetime.date): date
            nb(int): nb days to add
            exclude_we(bool): ignore week ends

        Returns:
            Arrow
        """
        d = cls._get(d)
        while nb > 0:
            d = d.shift(days=+1)
            if not exclude_we or not DateService.is_week_end(d):
                nb -= 1
        return d

    @classmethod
    def nb_days(cls, start, end, exclude_we=False):
        """
        Nb days between 2 dates
        Args:
            start(str|Arrow|datetime.datetime|datetime.date): start date
            end(str|Arrow|datetime.datetime|datetime.date): end date
            exclude_we(bool): ignore week ends

        Returns:

        """
        start = cls._get(start, default_now=False)
        end = cls._get(end, default_now=False)

        if not exclude_we:
            delta = end - start
            return delta.days

        nb = 0
        arrow_range = (
            arrow.Arrow.range("day", start, end)
            if start <= end
            else arrow.Arrow.range("day", end, start)
        )
        for d in arrow_range:
            if not cls.is_week_end(d):
                nb += 1

        if start <= end:
            return nb

        return nb * -1

    @classmethod
    def nb_years(cls, start, end):
        """
        Number of years between 2 dates
        Args:
            start(str|Arrow|datetime.datetime|datetime.date): start date
            end(str|Arrow|datetime.datetime|datetime.date): end date

        Returns:
            number of years: int
        """

        start = cls._get(start, default_now=False)
        end = cls._get(end, default_now=False)

        delta = relativedelta(end.datetime, start.datetime)
        return delta.years

    @classmethod
    def shift(cls, d, shifting_amount) -> Arrow:
        """
        Shift a date with the amount

        Args:
            d (str|Arrow|datetime.datetime|datetime.date): arrow date to shift from
            shifting_amount (dict):  shifting amount (use {years: 1, months:-1})

        Returns:
            Arrow: shifted date
        """
        d = cls._get(d, default_now=False)
        return d.shift(**shifting_amount)

    @classmethod
    def get_first_day_of_the_month(cls, d) -> Arrow:
        """
        Get the date of the first day of the month of a date

        Args:
            d (str|Arrow|datetime.datetime|datetime.date)

        Returns:
            Arrow
        """
        d = cls._get(d, default_now=False)
        return d.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @classmethod
    def parse(cls, naive_date: str, format: str, from_timezone: str | None = None):
        from_timezone = from_timezone or cls._timezone
        return arrow.get(naive_date, format).replace(tzinfo=from_timezone)

    @classmethod
    def _get(cls, d, default_now=True) -> Arrow:
        """
        Convert to arrow if necessary
        Args:
            d(None|str|Arrow|datetime.datetime|datetime.date): date, today if None

        Returns:
            Arrow
        """
        if default_now and d is None:
            return arrow.utcnow()

        if isinstance(d, Arrow):
            return d
        return arrow.get(d)

    @classmethod
    def _format(cls, d, date_format) -> str:
        """
        Format with timezone if set

        Args:
            d(None|str|Arrow|datetime.datetime|datetime.date): date, today if None
            date_format(string): string format

        Returns:
            str
        """
        if cls._timezone:
            return cls._get(d).to(cls._timezone).format(date_format, locale=cls._locale)
        return cls._get(d).format(fmt=date_format, locale=cls._locale)

    @staticmethod
    def _check_date_start_before_end(start, end):
        """
        Check if start if before end
        Args:
            start:
            end:

        Returns:

        """
        if end < start:
            raise RuntimeError("start must be before end")

    @classmethod
    def _get_start_end_and_validate_date(cls, start, end):
        """
        Get start, end date and check if start is before end
        Args:
            start:
            end:

        Returns:

        """
        start = cls._get(start, default_now=False)
        end = cls._get(end, default_now=False)
        cls._check_date_start_before_end(start, end)
        return start, end
