from django.db import models, transaction
from typing import List
from w.services.abstract_service import AbstractService
from w import exceptions


# noinspection PyCallingNonCallable
from w.services.technical.dict_service import DictService


class AbstractModelService(AbstractService):
    _model: models.Model

    @staticmethod
    def _is_field(field):
        """Check if field from model._meta.get_fields() is field"""
        return hasattr(field, "related_name") is False

    @classmethod
    def list_fields(cls) -> list:
        """List model fields"""
        return [f.name for f in cls._model._meta.get_fields() if cls._is_field(f)]

    @classmethod
    def clean_attrs(cls, attrs):  # pragma: no cover (todo one day)
        """Remove unexpected model attributes"""
        return DictService.keep_keys(attrs, cls.list_fields())

    @classmethod
    def create(cls, **attrs):
        """
        Create model instance

        Args:
            **attrs: model attributes values

        Returns:
            models.Model
        """
        instance = cls._model(**attrs)
        instance.save()
        return instance

    @classmethod
    def get_by_pk(cls, pk):  # pragma: no cover (todo one day)
        """
        Retrieve model by its primary key

        Returns:
            Model
        """
        return cls._model.objects.get(pk=pk)

    @classmethod
    def get_by_pk_and_select_related(
        cls, pk: int, select_related: List[str]
    ):  # pragma: no cover (todo one day)
        return cls._model.objects.select_related(*select_related).get(pk=pk)

    @classmethod
    def get_if_exists(cls, **filters):
        """Retrieve instance if exists else return None"""
        qs = cls._model.objects.filter(**filters)
        return qs.first()

    @classmethod
    def is_exists_by_pk(cls, pk) -> bool:  # pragma: no cover (todo one day)
        """
        Check model existsby its primary key

        Returns
            bool
        """
        qs = cls._model.objects.filter(pk=pk)
        return qs.exists()

    @classmethod
    def check_by_pk(cls, pk):
        """
        Check model exists by its primary key

        if found return model else raise NotFoundError

        Raises
            NotFoundError
        """
        try:
            return cls._model.objects.get(pk=pk)
        except cls._model.DoesNotExist:  # pragma: no cover (todo one day)
            label = cls._model._meta.verbose_name.title()  # noqa
            raise exceptions.NotFoundError(f"{label} not found (pk={pk})")

    @classmethod
    def list(cls, **filters) -> models.QuerySet:
        """
        List models filtered by filters (optional)

        Args:
            **filters: filter result

        Returns:
            QuerySet
        """
        if filters:  # pragma: no cover (todo one day)
            return cls._model.objects.filter(**filters)
        return cls._model.objects.all()

    @classmethod
    def list_pks(cls, **filters) -> List:  # pragma: no cover (todo one day)
        """
        List model pks filtered by filters (optional)

        Args:
            **filters:

        Returns:
            List
        """
        return cls.list(**filters).values_list("pk", flat=True)

    @classmethod
    def update(cls, instance, **attrs):
        """
        Update model instance

        Args:
            instance: model instance to update
            **attrs: model attributes values

        Returns:
            models.Model
        """
        update_it = False
        for attr, value in attrs.items():
            if getattr(instance, attr) != value:
                setattr(instance, attr, value)
                update_it = True

        if update_it:
            instance.save()
        return instance

    @classmethod
    def delete(cls, filters) -> int:
        """
        Delete

        Args:
            filters: model filters to delete

        Returns:
            nb deleted
        """
        nb, _ = cls._model.objects.filter(**filters).delete()
        return nb

    @classmethod
    def delete_by_pk(cls, pk) -> int:
        """
        Delete a model by is primary key

        Args:
            pk: model pk to delete

        Returns:
            nb deleted
        """
        return cls.delete({"pk": pk})

    @classmethod
    def to_dict(cls, instance):
        return {f: getattr(instance, f) for f in cls.list_fields()}

    @classmethod
    def get_or_create(cls, defaults=None, **kwargs):
        """
        Search for an existing instance with the given kwargs, creating a new one if
        necessary.
        Inspired by Django's get_or_create().
        Redefined here to be able to use custom create() of concerned model.

        Args:
            defaults(dict): additional fields to use for create operation
            # **kwargs: fields to be used to determine if instance already exists

        Returns:
            (instance, created): tuple of instance and a boolean specifying whether
                                 a new instance has been created or not.
        """
        instance = cls.get_if_exists(**kwargs)
        if instance is not None:
            return instance, False
        defaults = defaults or {}
        return cls.create(**{**kwargs, **defaults}), True

    @classmethod
    def update_or_create(cls, defaults=None, **kwargs):
        """
        Search for an existing instance with the given kwargs.
        If instance exists, update it. If not, create a new one.
        Inspired by Django's update_or_create().
        Redefined here to be able to use custom create() of concerned model.

        Args:
            defaults(dict): fields to update on existing instance or
                            additional fields to use for create operation
            **kwargs: fields to be used to determine if instance already exists

        Returns:
            (instance, created): tuple of instance and a boolean specifying whether
                                 a new instance has been created or not.
        """
        with transaction.atomic():
            instance, created = cls.get_or_create(defaults=defaults, **kwargs)
            is_update_needed = created is False and defaults is not None
            if is_update_needed:
                instance = cls.update(instance, **defaults)
                created = False
            return instance, created

    @classmethod
    def empty_and_reset_sequence(cls) -> None:  # pragma: no cover
        from django.db import connection
        from django.core.management.color import no_style

        if connection.vendor != "postgresql":  # pragma: no cover
            raise NotImplementedError("Only PostgreSQL supported for truncate")

        with transaction.atomic():
            cls._model.objects.all().delete()
            list_sql = connection.ops.sequence_reset_sql(no_style(), [cls._model])
            with connection.cursor() as cursor:
                for sql in list_sql:
                    cursor.execute(sql)
        return None

    @classmethod
    def bulk_create(
        cls, instances: List[models.Model]
    ) -> List[models.Model]:  # pragma: no cover
        return cls._model.objects.bulk_create(instances)
