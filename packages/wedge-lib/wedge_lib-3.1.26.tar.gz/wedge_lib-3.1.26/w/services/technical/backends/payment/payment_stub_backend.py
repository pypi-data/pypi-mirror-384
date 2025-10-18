from pathlib import Path


from w.services.technical.models.payment_models import (
    PaymentIntentCreation,
    PaymentIntent,
    PaymentResult,
    PaymentResultIn,
)
from w.test_utils.mixins.stub_backend_mixin import StubBackendMixin
from w.services.technical.backends.payment.abstract_payment_backend import (
    AbstractPaymentBackend,
)

_root_dir = Path(__file__).parent.parent.parent.parent.parent.parent


class PaymentStubBackend(StubBackendMixin, AbstractPaymentBackend):  # pragma: no cover
    _fixtures_path = _root_dir.joinpath("w/tests/fixtures/datasets/payment")
    _intent_id = "fake_intent_id"

    @classmethod
    def create_intent(cls, intent: PaymentIntentCreation) -> PaymentIntent:
        response = cls._call_stub()
        return PaymentIntent(**response)

    @classmethod
    def retrieve_payment_result(
        cls, payment_in: PaymentResultIn
    ) -> PaymentResult | None:
        response = cls._call_stub()
        if response is None:
            return None
        response["intent_id"] = cls._intent_id
        return PaymentResult(**response)

    @classmethod
    def set_current_intent_id(cls, intent_id: str):
        cls._intent_id = intent_id

    @classmethod
    def stub_retrieve_payment_result(cls, status: str = "success") -> dict:
        if status not in ["success", "failed"]:
            return cls.stub("retrieve_payment_result", None)
        return cls.stub_with_dataset("retrieve_payment_result", status)

    @classmethod
    def reset_stub(cls):
        super().reset_stub()
        cls._intent_id = "fake_intent_id"

    @classmethod
    def _is_initialized(cls) -> bool:
        name = "_is_initialized"
        if name in cls._stub:
            return cls._render_stub(name)
        return True
