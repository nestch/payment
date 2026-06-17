from __future__ import annotations

import uuid
from decimal import Decimal

import stripe
from sqlalchemy.orm import Session

from app.config import settings
from app.domain.credits import CREDIT_PACKAGES
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.repositories.payment_repository import PaymentRepository


def _to_stripe_amount(amount: Decimal) -> int:
    quantized = amount.quantize(Decimal("0.01"))
    return int(quantized * 100)


def create_checkout_session(
    *,
    payment_id: int,
    userID: int,
    amount: Decimal,
    currency: str,
    credits: Decimal,
    idempotency_key: str,
) -> stripe.checkout.Session:
    if not settings.stripe_secret_key:
        raise RuntimeError("Stripe is not configured (missing STRIPE_SECRET_KEY)")

    stripe.api_key = settings.stripe_secret_key

    session: stripe.checkout.Session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=[
            {
                "quantity": 1,
                "price_data": {
                    "currency": currency.lower(),
                    "unit_amount": _to_stripe_amount(amount),
                    "product_data": {"name": f"{credits} créditos"},
                },
            }
        ],
        success_url=settings.stripe_success_url,
        cancel_url=settings.stripe_cancel_url,
        metadata={
            "payment_id": str(payment_id),
            "userID": str(userID),
            "credits": str(credits),
        },
        client_reference_id=str(payment_id),
        idempotency_key=idempotency_key,
    )

    return session


def create_stripe_checkout_payment(
    db: Session,
    *,
    userID: int,
    credits: Decimal,
    currency: str,
) -> tuple[Payment, stripe.checkout.Session]:
    credits_key = f"{credits:.2f}"
    amount = CREDIT_PACKAGES.get(credits_key)
    if amount is None:
        raise ValueError(f"Unsupported credits package: {credits_key}")

    repo = PaymentRepository(db)

    payment = Payment(
        userID=userID,
        amount=amount,
        currency=currency,
        credits=credits,
        status=PaymentStatus.PENDING,
        method=PaymentMethod.CREDIT_CARD,
        transaction_id=None,
        idempotency_key=uuid.uuid4().hex,
    )
    repo.save(payment)

    try:
        session = create_checkout_session(
            payment_id=payment.id,
            userID=userID,
            amount=amount,
            currency=currency,
            credits=credits,
            idempotency_key=payment.idempotency_key,
        )
    except Exception:
        repo.delete(payment)
        raise

    payment.transaction_id = session.id
    repo.save(payment)

    return payment, session


def construct_webhook_event(*, payload: bytes, stripe_signature: str) -> stripe.Event:
    if not settings.stripe_webhook_secret:
        raise RuntimeError("Stripe webhook is not configured (missing STRIPE_WEBHOOK_SECRET)")

    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=stripe_signature,
        secret=settings.stripe_webhook_secret,
    )
