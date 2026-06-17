import hashlib
import uuid
from decimal import Decimal

from sqlalchemy.orm import Session

from app.config import settings
from app.messaging.rabbitmq import publish_message
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.repositories.payment_repository import PaymentRepository


def _make_idempotency_key(userID: int, amount: Decimal, currency: str, method: str) -> str:
    raw = f"{userID}:{amount}:{currency}:{method}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def create_payment_and_enqueue(
    db: Session,
    channel,
    *,
    userID: int,
    amount: Decimal,
    currency: str,
    method: str,
) -> Payment:
    idempotency_key = _make_idempotency_key(userID, amount, currency, method)

    repo = PaymentRepository(db)

    existing = repo.get_by_idempotency_key(idempotency_key)
    if existing is not None:
        return existing

    payment = Payment(
        userID=userID,
        amount=amount,
        currency=currency,
        status=PaymentStatus.PENDING,
        method=PaymentMethod(method),
        transaction_id=None,
        idempotency_key=idempotency_key,
    )
    repo.save(payment)

    message_id = str(uuid.uuid4())
    correlation_id = str(payment.id)

    publish_message(
        channel,
        routing_key=settings.rabbitmq_queue,
        payload={
            "payment_id": payment.id,
            "userID": payment.userID,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "method": payment.method.value,
        },
        message_id=message_id,
        correlation_id=correlation_id,
    )

    return payment
