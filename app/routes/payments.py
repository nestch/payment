from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.messaging.rabbitmq import ensure_topology, get_connection
from app.schemas.payments import PaymentCreateRequest, PaymentCreateResponse, PaymentRead
from app.security.jwt import require_auth
from app.services.payment_service import create_payment_and_enqueue
from app.models.payment import Payment


router = APIRouter(prefix="/payments", tags=["payments"])


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
            user_id=req.user_id,
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
        user_id=payment.user_id,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status.value,
        method=payment.method.value,
        transaction_id=payment.transaction_id,
    )
