from pydantic import BaseModel


class StripeSettings(BaseModel):
    secret_key: str
    webhook_secret: str


class StripePaymentResultIn(BaseModel):
    payload: bytes
    sig_header: str
