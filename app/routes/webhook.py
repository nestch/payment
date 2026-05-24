from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models.payment import Payment, PaymentStatus
from app.services.stripe_service import construct_webhook_event


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
    db: Session = Depends(get_db_session),
):
    if stripe_signature is None:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    payload = await request.body()

    try:
        event = construct_webhook_event(payload=payload, stripe_signature=stripe_signature)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    event_type = event.get("type")
    obj = event.get("data", {}).get("object", {})
    metadata = obj.get("metadata") or {}

    payment_id = metadata.get("payment_id")
    if payment_id is None and obj.get("client_reference_id"):
        payment_id = obj.get("client_reference_id")

    if payment_id is None:
        return {"received": True}

    payment: Payment | None = db.query(Payment).filter(Payment.id == int(payment_id)).one_or_none()
    if payment is None:
        return {"received": True}

    if event_type == "checkout.session.completed":
        payment.status = PaymentStatus.CONFIRMED
        if obj.get("payment_intent"):
            payment.transaction_id = obj.get("payment_intent")

    elif event_type in {"checkout.session.async_payment_failed", "payment_intent.payment_failed"}:
        payment.status = PaymentStatus.FAILED

    elif event_type in {"checkout.session.expired"}:
        payment.status = PaymentStatus.CANCELED

    db.add(payment)
    db.commit()

    return {"received": True}
