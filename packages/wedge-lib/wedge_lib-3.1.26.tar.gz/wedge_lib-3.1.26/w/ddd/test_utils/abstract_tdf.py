import random
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Any, Self, Type

from w.ddd.entity import Entity
from w.ddd.repository import Repository
from w.pydantics.date_models import DateTimeIn, DateTime
from w.test_utils.helpers import date_test_helper

EntityName = str


class AbstractTdf(ABC):  # pragma: no cover
    def __init__(
        self,
        start_id: int = 1,
        start_sequence: int = 1,
        today_is: DateTimeIn = "2025-06-02 11:21:46",
    ):
        self.today = DateTime(today_is)
        self.set_today_is(today_is)
        self._created: Dict = {}
        self._new: Dict = {}
        self._start_id = start_id
        self._start_sequence = start_sequence
        self._current_ids = {}
        self._sequence: Dict = {}
        random.seed(42)
        self._current_random_state = random.getstate()
        self._random_states: dict[str, Any] = {}

    def set_today_is(self, today_is: DateTimeIn | DateTime) -> Self:
        if isinstance(today_is, DateTimeIn):
            today_is = DateTime(today_is)

        self.today = today_is
        return self

    def random_decimal(
        self, min, max, randkey: str | None = None, precision: int | None = None
    ) -> Decimal:
        self._random_setstate(randkey)
        min = float(min)
        max = float(max)
        value = random.uniform(min, max)
        if precision is not None:
            value = round(value, precision)
        val = Decimal(str(value))
        self._save_current_random_state(randkey)
        return val

    def random_int(self, min, max, randkey: str | None = None) -> int:
        self._random_setstate(randkey)
        val = random.randrange(min, max)
        self._save_current_random_state(randkey)
        return val

    # def random_date(
    #     self, date_from: DateTimeIn, date_to: DateTimeIn, for_name: str | None = None
    # ) -> Date:
    #     # Vérifiez que la date de début est avant la date de fin
    #     d_from = Date(date_from)
    #     d_to = Date(date_to)
    #     if d_from > d_to:
    #         raise ValueError("The start date must be before the end date.")
    #     delta = d_to.to_datetime() - d_from.to_datetime()
    #     total_days = delta.days
    #     self._random_setstate(for_name)
    #     random_days = random.randint(0, total_days)
    #     self._save_current_random_state(for_name)
    #     random_date = d_from.shift({"days": random_days})
    #     return random_date

    def random_choice(self, choices: list[Any], randkey: str | None = None) -> Any:
        self._random_setstate(randkey)
        val = random.choice(choices)
        self._save_current_random_state(randkey)
        return val

    def reset_id(self, start_id: int = 1) -> None:
        self._start_id = start_id
        self._current_ids = {}

    def reset_sequence(self, start_sequence: int = 1) -> None:
        self._start_sequence = start_sequence
        self._sequence = {}

    def next_id(self, name: EntityName) -> int:
        if name not in self._current_ids:
            self._current_ids[name] = self._start_id
        else:
            self._current_ids[name] += 1
        return self._current_ids[name]

    def next_sequence(self, name: EntityName) -> int:
        if name not in self._sequence:
            self._sequence[name] = self._start_sequence
        else:
            self._sequence[name] += 1
        return self._sequence[name]

    def current_sequence(self, name: EntityName) -> int:
        return self._sequence[name]

    def get_current_id(self, name: EntityName) -> int:
        if name not in self._current_ids:
            return 0
        return self._current_ids[name]

    def list_created(self, name: str) -> list[Entity]:
        return self._created[name] if name in self._created else []

    def list_created_by_id(self, name: str) -> dict[str, list[Entity]]:
        return {c.id: c for c in self._created[name]} if name in self._created else {}

    @abstractmethod
    def persist_created(self): ...

    def persist(
        self, repository: Type[Repository], data: list[Entity] | Entity
    ) -> Self:
        if isinstance(data, list) is False:
            repository.create(data)
            return self

        for a in data:
            repository.create(a)
        return self

    def persist_new(self, name: str, repository: Type[Repository]) -> Self:
        for today_is, new_entities in self._list_new(name).items():
            with date_test_helper.today_is(today_is):
                self.persist(repository, new_entities)
        self._reset_new(name)
        return self

    def _list_new(self, name: str) -> dict[str, list[Entity]]:
        return self._new[name] if name in self._new else {}

    def _reset_new(self, name: str):
        self._new[name] = {}

    def _add_created(self, name: str, created: Entity):
        if name not in self._created:
            self._created[name] = []
            self._new[name] = {}

        self.today = self.today.shift({"seconds": 1})
        str_today = self.today.to_mysql_datetime()
        self._new[name][str_today] = []

        self._created[name].append(created)
        self._new[name][str_today].append(created)
        return created

    def _random_setstate(self, name: str | None = None) -> None:
        if name and name in self._random_states:
            random_state = self._random_states[name]
        else:
            random_state = self._current_random_state
        random.setstate(random_state)

    def _save_current_random_state(self, name: str | None = None) -> None:
        if name:
            self._random_states[name] = random.getstate()
            return None
        self._current_random_state = random.getstate()
        return None
