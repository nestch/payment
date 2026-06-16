import uuid
from decimal import Decimal
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.messaging.rabbitmq import ensure_topology, get_connection
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentRead,
    StripeCheckoutCreateRequest,
    StripeCheckoutCreateResponse,
)
from app.security.jwt import require_auth
from app.services.payment_service import create_payment_and_enqueue
from app.services.stripe_service import create_checkout_session


_logger = logging.getLogger(__name__)


router = APIRouter(prefix="/payments", tags=["payments"])


_CREDIT_PACKAGES: dict[str, Decimal] = {
    "10.00": Decimal("10.00"),
    "15.00": Decimal("15.00"),
    "20.00": Decimal("20.00"),
    "30.00": Decimal("30.00"),
    "40.00": Decimal("40.00"),
    "50.00": Decimal("50.00"),
}


@router.post("", response_model=PaymentCreateResponse)
def create_payment(
    req: PaymentCreateRequest,
    _payload: dict = Depends(require_auth),
    db: Session = Depends(get_db_session),
):
    try:
        connection = get_connection()
        channel = connection.channel()
        ensure_topology(channel)

        payment = create_payment_and_enqueue(
            db,
            channel,
            userID=req.userID,
            amount=req.amount,
            currency=req.currency,
            method=req.method,
        )
        return PaymentCreateResponse(id=payment.id, status=payment.status.value)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to create payment") from exc
    finally:
        try:
            connection.close()
        except Exception:
            pass


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(
    payment_id: int,
    _payload: dict = Depends(require_auth),
    db: Session = Depends(get_db_session),
):
    payment: Payment | None = db.query(Payment).filter(Payment.id == payment_id).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    return PaymentRead(
        id=payment.id,
        userID=payment.userID,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status.value,
        method=payment.method.value,
        transaction_id=payment.transaction_id,
    )


@router.post("/stripe/checkout", response_model=StripeCheckoutCreateResponse)
def create_stripe_checkout(
    req: StripeCheckoutCreateRequest,
    _payload: dict = Depends(require_auth),
    db: Session = Depends(get_db_session),
):
    credits_key = f"{req.credits:.2f}"
    amount = _CREDIT_PACKAGES.get(credits_key)
    if amount is None:
        raise HTTPException(status_code=400, detail="Unsupported credits package")

    payment = Payment(
        userID=req.userID,
        amount=amount,
        currency=req.currency,
        credits=req.credits,
        status=PaymentStatus.PENDING,
        method=PaymentMethod.CREDIT_CARD,
        transaction_id=None,
        idempotency_key=uuid.uuid4().hex,
    )

    db.add(payment)
    db.commit()
    db.refresh(payment)

    try:
        session = create_checkout_session(
            payment_id=payment.id,
            userID=req.userID,
            amount=amount,
            currency=req.currency,
            credits=req.credits,
            idempotency_key=payment.idempotency_key,
        )
    except Exception as exc:
        _logger.exception("Failed to create Stripe session")
        db.delete(payment)
        db.commit()
        raise HTTPException(status_code=500, detail="Failed to create Stripe session") from exc

    payment.transaction_id = session.id
    db.add(payment)
    db.commit()

    return StripeCheckoutCreateResponse(
        payment_id=payment.id,
        status=payment.status.value,
        checkout_url=session.url,
        stripe_session_id=session.id,
        payment_intent=session.payment_intent,
    )
