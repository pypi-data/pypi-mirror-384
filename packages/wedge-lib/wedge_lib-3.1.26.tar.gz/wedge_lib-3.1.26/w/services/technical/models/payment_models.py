from decimal import Decimal

from pydantic import BaseModel

from w.enums import StrEnum
from w.services.technical.backends.payment.models.stripe_models import (
    StripePaymentResultIn,
)


class PaymentBackend(StrEnum):
    stripe = "stripe"
    stub = "stub"


class PaymentCurrency(StrEnum):
    USD = "usd"
    EUR = "eur"
    KRW = "krw"


class PaymentIntentCreation(BaseModel):
    amount: Decimal
    currency: PaymentCurrency
    statement_descriptor: str | None = None
    metadata: dict[str, str] | None = None


PaymentResultIn = StripePaymentResultIn


class PaymentIntent(BaseModel):
    id: str
    status: str
    client_secret: str


class PaymentResultStatus(StrEnum):
    succeeded = "succeeded"
    payment_failed = "payment_failed"


class PaymentResult(BaseModel):
    intent_id: str
    status: PaymentResultStatus
    error: str | None = None
