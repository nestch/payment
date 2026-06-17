from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.domain.credits import credit_user, resolve_amount
from app.models.payment import Payment, PaymentMethod, PaymentStatus


def create_simulated_payment(
    db: Session,
    *,
    userID: int,
    credits: Decimal,
    currency: str,
) -> Payment:
    amount = resolve_amount(credits)

    payment = Payment(
        userID=userID,
        amount=amount,
        currency=currency,
        credits=credits,
        status=PaymentStatus.PENDING,
        method=PaymentMethod.PIX,
        transaction_id=None,
        idempotency_key=uuid.uuid4().hex,
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment


def confirm_simulated_payment(db: Session, payment: Payment) -> None:
    """Simula checkout.session.completed: CONFIRMED + creditsLedger + userTable."""
    payment.status = PaymentStatus.CONFIRMED
    payment.transaction_id = f"sim_pix_{uuid.uuid4().hex[:16]}"

    credit_user(db, payment=payment, stripe_event_id=f"sim_evt_{uuid.uuid4().hex}")

    db.add(payment)
    db.commit()


def fail_simulated_payment(db: Session, payment: Payment) -> None:
    """Simula checkout.session.async_payment_failed: FAILED."""
    payment.status = PaymentStatus.FAILED
    db.add(payment)
    db.commit()


def cancel_simulated_payment(db: Session, payment: Payment) -> None:
    """Simula checkout.session.expired: CANCELED."""
    payment.status = PaymentStatus.CANCELED
    db.add(payment)
    db.commit()
