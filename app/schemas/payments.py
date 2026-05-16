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


class HealthResponse(BaseModel):
    status: str
