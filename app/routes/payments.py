import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.messaging.rabbitmq import ensure_topology, get_connection
from app.repositories.payment_repository import PaymentRepository
from app.schemas.payments import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    PaymentRead,
    StripeCheckoutCreateRequest,
    StripeCheckoutCreateResponse,
)
from app.security.jwt import require_active_user
from app.services.payment_service import create_payment_and_enqueue
from app.services.stripe_service import create_stripe_checkout_payment


_logger = logging.getLogger(__name__)


router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("", response_model=PaymentCreateResponse)
def create_payment(
    req: PaymentCreateRequest,
    payload: dict = Depends(require_active_user),
    db: Session = Depends(get_db_session),
):
    try:
        connection = get_connection()
        channel = connection.channel()
        ensure_topology(channel)

        payment = create_payment_and_enqueue(
            db,
            channel,
            userID=payload["userID"],
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
    _payload: dict = Depends(require_active_user),
    db: Session = Depends(get_db_session),
):
    repo = PaymentRepository(db)
    payment = repo.get_by_id(payment_id)
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
    payload: dict = Depends(require_active_user),
    db: Session = Depends(get_db_session),
):
    try:
        payment, session = create_stripe_checkout_payment(
            db,
            userID=payload["userID"],
            credits=req.credits,
            currency=req.currency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        _logger.exception("Failed to create Stripe checkout")
        raise HTTPException(status_code=500, detail="Failed to create Stripe session") from exc

    return StripeCheckoutCreateResponse(
        payment_id=payment.id,
        status=payment.status.value,
        checkout_url=session.url,
        stripe_session_id=session.id,
        payment_intent=session.payment_intent,
    )
