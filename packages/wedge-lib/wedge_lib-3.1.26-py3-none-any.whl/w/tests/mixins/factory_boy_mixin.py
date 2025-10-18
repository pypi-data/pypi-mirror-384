from django.db import connection
from factory import SubFactory


class FactoryBoyMixin:
    """Mixin for FactoryBoy"""

    # factories list
    _factories = {}

    @classmethod
    def factory_reset_sequence(cls, facto, value=None):
        if value is None:
            value = 1
        # as we cannot reset descendant factories, reset parent
        # noinspection PyProtectedMember
        facto._meta.counter_reference.factory.reset_sequence(value)
        for attr, dec in facto._meta.declarations.items():
            if isinstance(dec, SubFactory):
                cls.factory_reset_sequence(dec.factory_wrapper.factory)

    @classmethod
    def reset_sequence(cls, value=1, reset_pk_model=False):
        value_not_model = value if value else 1
        if reset_pk_model:
            cls.reset_all_db_sequences()
        for name, factory in cls._factories.items():
            cls.factory_reset_sequence(factory, value_not_model)

    @classmethod
    def reset_all_db_sequences(cls):
        if connection.vendor != "postgresql":
            raise RuntimeError("connection not postgresql. reset_all canceled")

        sql = "SELECT c.relname FROM pg_class c WHERE c.relkind = 'S';"
        with connection.cursor() as c:
            c.execute(sql)
            results = c.fetchall()

            for sequence in results:
                sql = f"ALTER SEQUENCE {sequence[0]} RESTART 1;"
                c.execute(sql)

    @classmethod
    def _check_factory_exists(cls, factory_key):
        if factory_key not in cls._factories:
            raise RuntimeError(
                f"{factory_key} missing, add it to {__class__}._factories"
            )

    @classmethod
    def create(cls, factory_key, nb=1, **kwargs):
        cls._check_factory_exists(factory_key)
        return (
            cls._factories[factory_key](**kwargs)
            if nb == 1
            else cls._factories[factory_key].create_batch(nb, **kwargs)
        )

    @classmethod
    def build_as_dict(cls, factory_key, **kwargs):
        cls._check_factory_exists(factory_key)
        return cls._factories[factory_key].stub(**kwargs).__dict__
