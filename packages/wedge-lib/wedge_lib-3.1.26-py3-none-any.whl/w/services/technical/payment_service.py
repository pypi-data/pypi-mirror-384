from typing import Type

from w.services.abstract_service import AbstractService
from w.services.technical.models.payment_models import (
    PaymentBackend,
    PaymentIntentCreation,
    PaymentIntent,
    PaymentResultIn,
    PaymentResult,
)
from w.services.technical.backends.payment.abstract_payment_backend import (
    AbstractPaymentBackend,
)
from w.utils import import_path


class PaymentService(AbstractService):
    _backend: Type[AbstractPaymentBackend] | None = None

    @classmethod
    def initialize(cls, backend: PaymentBackend) -> None:
        cls.clear()
        cls._backend = import_path(cls._get_backend_path(backend))

    @classmethod
    def create_intent(cls, intent: PaymentIntentCreation) -> PaymentIntent:
        cls._check_is_initialized()
        return cls._backend.create_intent(intent)

    @classmethod
    def retrieve_payment_result(cls, payment_in: PaymentResultIn) -> PaymentResult:
        cls._check_is_initialized()
        return cls._backend.retrieve_payment_result(payment_in)

    @classmethod
    def clear(cls):
        cls._backend = None

    @classmethod
    def _is_initialized(cls):
        return cls._backend is not None and cls._backend._is_initialized()

    @classmethod
    def _get_backend_path(cls, backend: PaymentBackend) -> str:
        return (
            "w.services.technical.backends.payment"
            f".payment_{backend.value}_backend"
            f".Payment{backend.value.capitalize()}Backend"
        )
