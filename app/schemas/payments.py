from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


PaymentMethod = Literal["CREDIT_CARD", "PIX", "BOLETO", "PAYPAL"]
PaymentStatus = Literal["PENDING", "CONFIRMED", "FAILED", "CANCELED"]


class PaymentCreateRequest(BaseModel):
    user_id: int = Field(gt=0)
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    method: PaymentMethod


class PaymentCreateResponse(BaseModel):
    id: int
    status: PaymentStatus


class PaymentRead(BaseModel):
    id: int
    user_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    method: PaymentMethod
    transaction_id: str | None


class StripeCheckoutCreateRequest(BaseModel):
    user_id: int = Field(gt=0)
    credits: Decimal = Field(gt=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)


class StripeCheckoutCreateResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
    checkout_url: str
    stripe_session_id: str
    payment_intent: str | None


class HealthResponse(BaseModel):
    status: str


# ---------------------------------------------------------------------------
# Simulate endpoints
# ---------------------------------------------------------------------------

SimulateOutcome = Literal["success", "failure", "cancel"]


class SimulateCheckoutRequest(BaseModel):
    user_id: int = Field(gt=0)
    credits: Decimal = Field(gt=0)
    currency: str = Field(default="BRL", min_length=3, max_length=3)
    simulate: SimulateOutcome = Field(
        default="success",
        description="'success' → CONFIRMED, 'failure' → FAILED, 'cancel' → CANCELED",
    )


class SimulateCheckoutResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
    simulated_event: str
    transaction_id: str | None


class SimulateCallbackRequest(BaseModel):
    payment_id: int = Field(gt=0)
    simulate: SimulateOutcome = Field(
        description="'success' → CONFIRMED, 'failure' → FAILED, 'cancel' → CANCELED",
    )


class SimulateCallbackResponse(BaseModel):
    payment_id: int
    status: PaymentStatus
    simulated_event: str
