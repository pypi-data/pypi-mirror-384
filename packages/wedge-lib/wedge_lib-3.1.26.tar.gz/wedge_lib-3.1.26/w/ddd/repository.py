from abc import abstractmethod
from typing import Type

from django.db.models import Model, QuerySet

from w.ddd.entity import Entity, EntityId, RawItem
from w.services.abstract_model_service import AbstractModelService
from w.services.abstract_service import AbstractService
from django.forms.models import model_to_dict


class Repository[E: Entity](AbstractService):
    @classmethod
    def create(cls, entity: E) -> None:
        raw_data = cls._entity_to_raw(entity)
        raw_data["pk"] = raw_data.pop("id")
        cls._get_db_service().create(**raw_data)
        return None

    @classmethod
    def update(cls, entity: E) -> None:
        raw_data = cls._entity_to_raw(entity)
        pk = raw_data.pop("id")
        db_model = cls._get_db_service().check_by_pk(pk=pk)
        cls._get_db_service().update(db_model, **raw_data)
        return None

    @classmethod
    def delete(cls, entity: E) -> None:
        cls._get_db_service().delete_by_pk(entity.id)
        return None

    @classmethod
    def get_by_id(cls, id: EntityId) -> E | None:
        return cls.get_by_filters(pk=id)

    @classmethod
    def check_by_id(cls, id: EntityId) -> E:
        return cls._hydrate(cls._get_db_service().check_by_pk(pk=id))

    @classmethod
    def get_by_filters(cls, **filters) -> E | None:
        return cls._hydrate(cls._get_db_service().get_if_exists(**filters))

    @classmethod
    def list_all(cls) -> list[E]:
        return cls._hydrate_many(cls._get_db_service().list())

    @classmethod
    def list_by_filters(cls, **filters) -> list[E]:
        return cls._hydrate_many(cls._get_db_service().list(**filters))

    @classmethod
    def _entity_to_raw(cls, entity: E) -> RawItem:
        return entity.model_dump()

    @classmethod
    def _hydrate(cls, db_model: Model | None) -> E | None:
        if db_model is None:
            return None
        return cls._get_entity_class()(**cls._db_to_raw(db_model))

    @classmethod
    def _hydrate_many(cls, db_models: QuerySet) -> list[E]:
        return [cls._hydrate(db_model) for db_model in db_models]

    @classmethod
    def _db_to_raw(cls, db_model: Model) -> dict:
        raw = model_to_dict(db_model)
        raw["id"] = db_model.pk
        return raw

    @classmethod
    @abstractmethod
    def _get_db_service(cls) -> Type[AbstractModelService]: ...

    @classmethod
    @abstractmethod
    def _get_entity_class(cls) -> type[E]: ...
