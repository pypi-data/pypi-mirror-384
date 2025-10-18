from abc import abstractmethod, ABC

from w.services.technical.models.payment_models import (
    PaymentIntentCreation,
    PaymentIntent,
    PaymentResult,
    PaymentResultIn,
)


class AbstractPaymentBackend(ABC):
    @classmethod
    @abstractmethod
    def create_intent(cls, intent: PaymentIntentCreation) -> PaymentIntent: ...

    @classmethod
    def retrieve_payment_result(
        cls, payment_in: PaymentResultIn
    ) -> PaymentResult | None: ...

    @classmethod
    @abstractmethod
    def _is_initialized(cls) -> bool: ...
