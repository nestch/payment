from __future__ import annotations

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.payment import Payment


CREDIT_PACKAGES: dict[str, Decimal] = {
    "10.00": Decimal("10.00"),
    "15.00": Decimal("15.00"),
    "20.00": Decimal("20.00"),
    "30.00": Decimal("30.00"),
    "40.00": Decimal("40.00"),
    "50.00": Decimal("50.00"),
}


def resolve_amount(credits: Decimal) -> Decimal:
    credits_key = f"{credits:.2f}"
    amount = CREDIT_PACKAGES.get(credits_key)
    if amount is None:
        raise ValueError(f"Unsupported credits package: {credits_key}")
    return amount


def credit_user(db: Session, *, payment: Payment, stripe_event_id: str) -> None:
    credits_val: Decimal = payment.credits if payment.credits is not None else Decimal("0")

    if credits_val <= 0 or payment.credited_at is not None:
        return

    db.execute(
        text(
            "INSERT IGNORE INTO creditsLedger "
            "(userID, payment_id, credits, amount_paid, stripe_event_id) "
            "VALUES (:userID, :payment_id, :credits, :amount_paid, :stripe_event_id)"
        ),
        {
            "userID": payment.userID,
            "payment_id": payment.id,
            "credits": credits_val,
            "amount_paid": payment.amount,
            "stripe_event_id": stripe_event_id,
        },
    )
    db.execute(
        text(
            "UPDATE userTable "
            "SET credit = COALESCE(credit, 0) + :credits "
            "WHERE userID = :userID"
        ),
        {"credits": credits_val, "userID": payment.userID},
    )
    db.execute(
        text("UPDATE paymentsTable SET credited_at = NOW() WHERE id = :payment_id"),
        {"payment_id": payment.id},
    )
