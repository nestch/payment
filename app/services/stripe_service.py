from __future__ import annotations

from decimal import Decimal

import stripe

from app.config import settings


def _to_stripe_amount(amount: Decimal) -> int:
    quantized = amount.quantize(Decimal("0.01"))
    return int(quantized * 100)


def create_checkout_session(
    *,
    payment_id: int,
    user_id: int,
    amount: Decimal,
    currency: str,
    credits: int,
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
            "user_id": str(user_id),
            "credits": str(credits),
        },
        client_reference_id=str(payment_id),
        idempotency_key=idempotency_key,
    )

    return session


def construct_webhook_event(*, payload: bytes, stripe_signature: str) -> stripe.Event:
    if not settings.stripe_webhook_secret:
        raise RuntimeError("Stripe webhook is not configured (missing STRIPE_WEBHOOK_SECRET)")

    return stripe.Webhook.construct_event(
        payload=payload,
        sig_header=stripe_signature,
        secret=settings.stripe_webhook_secret,
    )
