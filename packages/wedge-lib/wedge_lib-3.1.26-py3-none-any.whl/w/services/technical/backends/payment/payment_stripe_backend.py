import stripe

from w.services.technical.backends.payment.models.stripe_models import (
    StripeSettings,
    StripePaymentResultIn,
)
from w.services.technical.models.payment_models import (
    PaymentIntentCreation,
    PaymentIntent,
    PaymentResult,
    PaymentResultStatus,
)
from w.services.technical.backends.payment.abstract_payment_backend import (
    AbstractPaymentBackend,
)
import logging

logger = logging.getLogger(__name__)


class PaymentStripeBackend(AbstractPaymentBackend):
    _settings: StripeSettings | None = None
    _handle_payment_event_types = [
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
    ]

    @classmethod
    def initialize(cls, settings: StripeSettings) -> None:
        cls._settings = settings
        stripe.api_key = settings.secret_key

    @classmethod
    def create_intent(cls, intent: PaymentIntentCreation) -> PaymentIntent:
        cls._check_is_initialized()
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(intent.amount * 100),
                currency=intent.currency.value.lower(),
            )
        except Exception as e:
            raise RuntimeError(f"create payment intent failed: {e}")
        return PaymentIntent(
            id=payment_intent["id"],
            status=payment_intent["status"],
            client_secret=payment_intent["client_secret"],
        )

    @classmethod
    def retrieve_payment_result(
        cls, payment_in: StripePaymentResultIn
    ) -> PaymentResult | None:
        cls._check_is_initialized()
        try:
            event = stripe.Webhook.construct_event(
                payment_in.payload, payment_in.sig_header, cls._settings.webhook_secret
            )
            logger.debug(f"Payment result: {event}")
        except Exception as e:
            raise RuntimeError(f"retrieve payment result failed: {e}")

        event_dict = event.to_dict()
        event_type = event_dict["type"]

        if event_type not in cls._handle_payment_event_types:
            # ignore not handled event types
            logger.info(f"Stripe payment event type {event_dict['type']} is ignored")
            return None

        intent = event_dict["data"]["object"]
        if event_type == "payment_intent.succeeded":
            return PaymentResult(
                intent_id=intent["id"], status=PaymentResultStatus.succeeded
            )
        logger.info(f"Stripe payment (intent_id={intent['id']}) has failed")
        error_message = (
            intent["last_payment_error"]["message"]
            if intent.get("last_payment_error")
            else None
        )
        return PaymentResult(
            intent_id=intent["id"],
            status=PaymentResultStatus.payment_failed,
            error=error_message,
        )

    @classmethod
    def _is_initialized(cls) -> bool:
        return cls._settings is not None

    @classmethod
    def _check_is_initialized(cls):
        if cls._is_initialized():
            return None

        raise RuntimeError(f"{cls.__name__} must be initialized first")

    @classmethod
    def clear(cls) -> None:
        cls._settings = None
