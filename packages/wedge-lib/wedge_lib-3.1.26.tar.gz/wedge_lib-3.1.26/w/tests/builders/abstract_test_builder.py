from abc import ABC
from typing import Dict

from django.db import models
from w.services.technical.date_service import DateService
from w.tests.helpers import date_test_helper
from w.tests.mixins.factory_boy_mixin import FactoryBoyMixin


class AbstractTestBuilder(FactoryBoyMixin, ABC):
    _factories: Dict = {}
    _main_factory_key = None
    _related_built: Dict = {}

    @classmethod
    def _check_factory_exists(cls, factory_key):
        if factory_key not in cls._factories:
            raise RuntimeError(
                f"{factory_key} missing, add it to {__class__}._factories"
            )

    @classmethod
    def get_factory(cls, factory_key):
        cls._check_factory_exists(factory_key)
        return cls._factories[factory_key]

    def __init__(self):
        # attributes to use with main factory
        self._attrs = {}
        # attributes to build for foreign key factories
        self._fk_factories_attrs = {}
        # builder for foreign key
        self._fk_builders = {}
        # related factories and its attributes
        self._related_factories_attrs = {}
        # define today date
        self._date_today = None

    def _complete_attrs(self, attrs):
        """
        For each registered factories, build attribute from factory and add it to
        attrs

        Args:
            attrs:

        Returns:
            dict
        """
        attrs = {**self._attrs, **attrs}

        for attr, params in self._fk_factories_attrs.items():
            attrs[attr] = self.get_factory(params["key"])(**params["attrs"])

        for attr, builder in self._fk_builders.items():
            attrs[attr] = builder.build()

        return attrs

    def _set_foreign_key_factory_attrs(
        self, attr: str, factory_attrs: dict, factory_key=None
    ):
        """
        Define foreign key factory
        Args:
            attr(str): foreign key attribute
            factory_attrs(dict): attributes for factory
            factory_key(str|None): if None factory_key = attr
        """
        if factory_key is None:
            factory_key = attr
        self._fk_factories_attrs[attr] = {"key": factory_key, "attrs": factory_attrs}

    def _set_foreign_key_builder(self, attr: str, builder):
        self._fk_builders[attr] = builder

    def _create_related_factory_if_missing(self, attr: str, factory_key=None):
        if factory_key is None:
            factory_key = attr
        if attr not in self._related_factories_attrs:
            self._related_factories_attrs[attr] = {"key": factory_key, "list_attrs": []}

    def _add_related_factory_attrs(
        self, attr: str, factory_attrs: dict, factory_key=None
    ):
        self._create_related_factory_if_missing(attr, factory_key)
        self._related_factories_attrs[attr]["list_attrs"].append(factory_attrs)

    def _set_related_factory_attrs(
        self, attr: str, list_factory_attrs: list, factory_key=None
    ):
        self._create_related_factory_if_missing(attr, factory_key)
        self._related_factories_attrs[attr]["list_attrs"] += list_factory_attrs

    def _set_nb_related_factory_attrs(
        self, attr: str, nb, factory_attrs: dict, factory_key=None
    ):
        self._create_related_factory_if_missing(attr, factory_key)
        for _ in range(nb):
            self._related_factories_attrs[attr]["list_attrs"].append(factory_attrs)

    def _build_related_factory(self, factory_key, factory_attrs, related_attrs):
        factory_attrs = {**factory_attrs, **related_attrs}
        return self.get_factory(factory_key)(**factory_attrs)

    def _build_related_factories(self, related_attrs: dict) -> dict:
        """
        Build related factories linked on linked_attrs
        Args:
            related_attrs(dict): {<related_attr>: value, ...}

        Returns:
            dict: list built models by factory_key
        """
        factory_builds = {}
        for attr, params in self._related_factories_attrs.items():
            factory_builds[attr] = []
            for factory_attrs in params["list_attrs"]:
                factory_builds[attr].append(
                    self._build_related_factory(
                        params["key"], factory_attrs, related_attrs
                    )
                )
        return factory_builds

    def _get_related_built(self, factory_key: str) -> list:
        return self._related_built[factory_key]

    @classmethod
    def list_used_builders(cls):
        """List builders used by this builder for test reset sequence"""
        return [cls]

    def with_today_is(self, date):
        """
        Force today to be date

        Args:
            date (str|Arrow|datetime.datetime|datetime.date): date today

        Returns:
            self
        """
        self._date_today = DateService.to_datetime(date)
        return self

    def with_attrs(self, **attrs):
        """
        Define main attributes
        """
        self._attrs = {**self._attrs, **attrs}
        return self

    def _build(self, attrs):
        main_built = self.get_factory(self._main_factory_key)(**attrs)
        self._related_built = self._build_related_factories(
            {self._main_factory_key: main_built}
        )
        return main_built

    def build(self, **attrs):
        """
        Build main model
        """
        if self._main_factory_key is None:
            raise RuntimeError("You must define '_main_factory_key' in your builder")

        attrs = self._complete_attrs(attrs)

        if self._date_today:
            with date_test_helper.today_is(self._date_today):
                return self._build(attrs)

        return self._build(attrs)

    def build_multiple(self, nb, **attrs):
        """Build multiple"""
        builds = []
        for _ in range(0, nb):
            builds.append(self.build(**attrs))
        return builds

    @staticmethod
    def _is_django_model(value) -> bool:
        """Check if value is django model"""
        return isinstance(value, models.Model)

    def build_create_data(self, **attrs) -> dict:
        """Build create/update data from main factory"""
        import factory

        attrs = self._complete_attrs(attrs)
        factory_class = self.get_factory(self._main_factory_key)

        # looking for SubFactory to build them
        list_attrs = [
            a
            for a in factory_class.__dict__.keys()
            if not a.startswith("_") and a not in attrs
        ]
        for attr in list_attrs:
            value = getattr(factory_class, attr)
            if isinstance(value, factory.SubFactory):
                attrs[attr] = value.factory_wrapper.factory()

        return factory.build(dict, FACTORY_CLASS=factory_class, **attrs)

    def build_post_data(self, **attrs) -> dict:
        """Build post data from main factory"""
        if self._date_today is None:
            built = self.build_create_data(**attrs)
        else:
            with date_test_helper.today_is(self._date_today):
                built = self.build_create_data(**attrs)

        result = {}
        for attr, value in built.items():
            # remove foreign key object
            if self._is_django_model(value):
                result[f"{attr}"] = value.pk
            else:
                result[attr] = value

        return result
