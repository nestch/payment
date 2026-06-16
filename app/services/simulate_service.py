from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.payment import Payment, PaymentMethod, PaymentStatus


_CREDIT_PACKAGES: dict[str, Decimal] = {
    "10.00": Decimal("10.00"),
    "15.00": Decimal("15.00"),
    "20.00": Decimal("20.00"),
    "30.00": Decimal("30.00"),
    "40.00": Decimal("40.00"),
    "50.00": Decimal("50.00"),
}


def create_simulated_payment(
    db: Session,
    *,
    user_id: int,
    credits: Decimal,
    currency: str,
) -> Payment:
    credits_key = f"{credits:.2f}"
    amount = _CREDIT_PACKAGES.get(credits_key)
    if amount is None:
        raise ValueError(f"Unsupported credits package: {credits_key}")

    payment = Payment(
        user_id=user_id,
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

    credits_val: Decimal = payment.credits if payment.credits is not None else Decimal("0")

    if credits_val > 0 and payment.credited_at is None:
        db.execute(
            text(
                "INSERT IGNORE INTO creditsLedger "
                "(user_id, payment_id, credits, amount_paid, stripe_event_id) "
                "VALUES (:user_id, :payment_id, :credits, :amount_paid, :stripe_event_id)"
            ),
            {
                "user_id": payment.user_id,
                "payment_id": payment.id,
                "credits": credits_val,
                "amount_paid": payment.amount,
                "stripe_event_id": f"sim_evt_{uuid.uuid4().hex}",
            },
        )
        db.execute(
            text(
                "UPDATE userTable "
                "SET credit = COALESCE(credit, 0) + :credits "
                "WHERE userID = :user_id"
            ),
            {"credits": credits_val, "user_id": payment.user_id},
        )
        db.execute(
            text("UPDATE paymentsTable SET credited_at = NOW() WHERE id = :payment_id"),
            {"payment_id": payment.id},
        )

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
