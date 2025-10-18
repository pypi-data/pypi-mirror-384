import copy
from dataclasses import field, dataclass
from os import path
from typing import Optional

from django.db.models import Prefetch, QuerySet, Model
from django.utils.translation import gettext as _
from pydantic import BaseModel
from serpy import *

from w.services.technical.date_service import DateService


class DateField(Field):
    def to_value(self, value):
        if value:
            return DateService.to_mysql_date(value)


class DatetimeField(Field):
    def to_value(self, value):
        if value:
            return DateService.to_mysql_datetime(value)


class ManyToManyField(Field):
    def __init__(self, serializer, attr=None, call=False, label=None, required=True):
        super().__init__(attr, call, label, required)
        self.serializer = serializer

    def to_value(self, value):
        if value and value.exists():
            return self.serializer(value.all(), many=True).data
        return []


class ManyToFirstField(ManyToManyField):  # pragma: no cover (todo one day)
    def to_value(self, value):
        if value and value.exists():
            # for queryset optimization is better to do value.all() than value.first() ?!
            data = self.serializer(value.all(), many=True).data
            return data[0]
        return None


class PhoneNumberField(Field):  # pragma: no cover (todo one day)
    def to_value(self, value):
        if value:
            return value.as_e164


class FileField(Field):  # pragma: no cover (todo one day)
    def to_value(self, value):
        return value.name if value else None


class BasenameFileField(Field):  # pragma: no cover (todo one day)
    def to_value(self, value):
        return path.basename(value.name) if value else None


class TranslateField(Field):  # pragma: no cover (todo one day)
    def to_value(self, value):
        return _(value) if value else ""


class CloudinaryField(Field):  # pragma: no cover (todo one day)
    def to_value(self, value):
        return value.url if value else None


class PydanticField(Field):  # pragma: no cover (todo one day)
    def to_value(self, value: BaseModel):
        return value.model_dump() if value else None


@dataclass
class QueryOptimization:
    parent_attr: Optional[str] = None
    model: Optional[Model] = None
    foreign_keys: list = field(default_factory=list)
    many2manies: list = field(default_factory=list)

    def _get_select_related(self):
        select_related = []
        for foreign_key in self.foreign_keys:
            child_related = foreign_key._get_select_related()
            if self.parent_attr:
                select_related += [f"{self.parent_attr}__{r}" for r in child_related]
            else:
                select_related += child_related
        if self.parent_attr:
            select_related += [self.parent_attr]
        return select_related

    def _get_prefetch_related(self):
        prefetch_related = []
        for many2many in self.many2manies:
            if many2many.is_not_empty():
                query_optimization = copy.deepcopy(many2many)
                query_optimization.parent_attr = None
                child_qs = query_optimization.get_optimized_queryset(
                    query_optimization.model.objects
                )
                prefetch_related.append(
                    Prefetch(many2many.parent_attr, queryset=child_qs)
                )
            else:
                prefetch_related.append(Prefetch(many2many.parent_attr))
        return prefetch_related

    def get_optimized_queryset(self, qs: QuerySet):
        prefetch_related = self._get_prefetch_related()
        if prefetch_related:
            qs = qs.prefetch_related(*prefetch_related)
        select_related = self._get_select_related()
        if select_related:
            qs = qs.select_related(*select_related)

        return qs

    def is_not_empty(self):
        return self.foreign_keys or self.many2manies


class SerpySerializer(Serializer):
    """
    Data serializer built on Serpy.

    It adds query_string optimization and add custom Fields

    @see serpy documentation
    """

    _prepared_optimization = None

    class Meta:
        abstract = True

    @classmethod
    def _prepare_optimization(cls, parent_attr=None) -> QueryOptimization:
        query_optimization = QueryOptimization(
            parent_attr=parent_attr, model=cls.get_model()
        )
        for attr, serializer_field in cls._field_map.items():
            parent_attr = serializer_field.attr if serializer_field.attr else attr
            if isinstance(serializer_field, SerpySerializer):
                # fk
                query_optimization.foreign_keys.append(
                    serializer_field._prepare_optimization(parent_attr=parent_attr)
                )
                continue
            if isinstance(serializer_field, ManyToManyField) or isinstance(
                serializer_field, ManyToFirstField
            ):
                # manyToMany
                query_optimization.many2manies.append(
                    serializer_field.serializer._prepare_optimization(
                        parent_attr=parent_attr
                    )
                )

        for parent_attr, serializer in cls._foreign_keys().items():
            query_optimization.foreign_keys.append(
                serializer._prepare_optimization(parent_attr=parent_attr)
            )

        for parent_attr, serializer in cls._many2many().items():
            query_optimization.many2manies.append(
                serializer._prepare_optimization(parent_attr=parent_attr)
            )

        return query_optimization

    @classmethod
    def get_optimized_queryset(cls, qs=None, prefix_related=None) -> QuerySet:
        """
        Get optimal QuerySet for serialization

        Args:
            qs (QuerySet): query set to complete
            prefix_related (str): prefix to add (for internal usage)

        Returns:
            QuerySet
        """

        if qs is None:
            qs = cls.get_qs()
        query_optimization = cls._prepare_optimization()
        return query_optimization.get_optimized_queryset(qs)

    @classmethod
    def get_model(cls):  # pragma: no cover (todo one day)
        if hasattr(cls.Meta, "model"):
            return cls.Meta.model
        raise RuntimeError(f"No model set on {cls.__module__}.{cls.__name__}.Meta")

    @classmethod
    def get_qs(cls):
        return cls.get_model().objects.all()

    @classmethod
    def _foreign_keys(cls) -> dict:
        return {}

    @classmethod
    def _many2many(cls) -> dict:
        return {}
