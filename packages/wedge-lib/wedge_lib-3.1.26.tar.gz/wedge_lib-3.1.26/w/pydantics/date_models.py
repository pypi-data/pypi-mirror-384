import datetime
from abc import ABC
from typing import Union, Annotated, Self

import arrow
from arrow import Arrow
from pydantic import (
    RootModel,
    BeforeValidator,
    ConfigDict,
    model_validator,
    model_serializer,
)

DateTimeIn = Union[str, datetime.datetime, datetime.date, int, float, Arrow]


def validate_from_in(value: DateTimeIn, error_msg: str) -> DateTimeIn:
    if isinstance(value, Arrow):
        return value
    try:
        arrow.get(value)
        return value
    except (TypeError, arrow.parser.ParserError):
        raise ValueError(error_msg)


def validate_datetime_in(value: DateTimeIn) -> DateTimeIn:
    return validate_from_in(value, "datetime invalid (YYYY-MM-DD HH:mm:ss.SSSSSS)")


def validate_date_in(value: DateTimeIn) -> DateTimeIn:
    return validate_from_in(value, "date invalid (YYYY-MM-DD)")


class AbstractDate(ABC):
    _internal_value: Arrow
    _timezone: str = "UTC"
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_mysql_date(self) -> str:
        return self._format("YYYY-MM-DD")

    def to_mysql_datetime(self) -> str:
        return self._format("YYYY-MM-DD HH:mm:ss.SSSSSS")

    def to_date(self) -> datetime.date:
        return self._internal_value.date()

    def to_datetime(self) -> datetime.datetime:
        return self._internal_value.to(self._timezone).datetime  # type: ignore

    def to_timestamp(self) -> float:
        return self._internal_value.timestamp()

    def format(self, format: str, timezone: str | None = None) -> str:
        return self._format(format, timezone)

    def _root_to_arrow(self) -> Arrow:
        return self.root if isinstance(self.root, Arrow) else arrow.get(self.root)  # type: ignore # noqa: E501

    def __eq__(self, other):
        return self._internal_value == other._internal_value

    def __ne__(self, other):
        return self._internal_value != other._internal_value

    def __ge__(self, other):
        return self._internal_value >= other._internal_value

    def __le__(self, other):
        return self._internal_value <= other._internal_value

    def __gt__(self, other):
        return self._internal_value > other._internal_value

    def __lt__(self, other):
        return self._internal_value < other._internal_value

    def __sub__(self, other):
        return self._internal_value - other._internal_value

    def _format(self, date_format, timezone: str | None = None) -> str:
        return self._internal_value.to(timezone or self._timezone).format(date_format)

    @classmethod
    def now(cls) -> "DateTime":
        return cls(arrow.utcnow())

    def to_timezone(self, timezone: str) -> "DateTime":
        return DateTime(self._internal_value.to(timezone))

    @property
    def year(self) -> int:
        return self._internal_value.year


class DateTime(AbstractDate, RootModel):
    root: Annotated[DateTimeIn, BeforeValidator(validate_datetime_in)]

    @model_validator(mode="after")
    def to_arrow(self) -> Self:
        self._internal_value = self._root_to_arrow()
        return self

    @model_serializer()
    def serialize(self):
        return self.to_mysql_datetime()

    @classmethod
    def parse(cls, value: str, format: str) -> "DateTime":
        return cls(arrow.get(value, format))

    def shift(self, shifting_amount: dict) -> "DateTime":
        """
        Shift a date with the amount

        Args:
            d (str|Arrow|datetime.datetime|datetime.date): arrow date to shift from
            shifting_amount (dict):  shifting amount (use {years: 1, months:-1})
        Returns:
            DateTime : shifted date
        """
        return DateTime(self._internal_value.shift(**shifting_amount))

    def reset_microseconds(self) -> "DateTime":
        """
        Reset milliseconds to 0
        """
        return DateTime(self._internal_value.replace(microsecond=0))

    def __repr__(self):
        return str(self)  # pragma: no cover

    def __str__(self):
        return str(self._internal_value)


class Date(AbstractDate, RootModel):
    root: Annotated[DateTimeIn, BeforeValidator(validate_date_in)]

    @model_serializer()
    def serialize(self):
        return self.to_mysql_date()

    @model_validator(mode="after")
    def to_arrow(self) -> Self:
        arrow_date = self._root_to_arrow()
        # to be sure to remove time informations
        self._internal_value = arrow.get(arrow_date.date())
        return self

    @classmethod
    def parse(cls, value: str, format: str) -> "Date":
        return cls(arrow.get(value, format))

    def shift(self, shifting_amount: dict) -> "Date":
        return Date(self._internal_value.shift(**shifting_amount))

    def __repr__(self):
        return str(self)  # pragma: no cover

    def __str__(self):
        return str(self._internal_value)  # pragma: no cover
