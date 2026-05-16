import json
import time
from decimal import Decimal

import pika
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.messaging.rabbitmq import ensure_topology, get_connection
from app.models.payment import Payment, PaymentStatus


def _process_message(db: Session, payload: dict) -> None:
    payment_id = int(payload["payment_id"])

    payment: Payment | None = db.query(Payment).filter(Payment.id == payment_id).one_or_none()
    if payment is None:
        return

    if payment.status != PaymentStatus.PENDING:
        return

    payment.status = PaymentStatus.CONFIRMED
    payment.transaction_id = payment.transaction_id or f"mock-{payment.id}"
    db.add(payment)
    db.commit()


def callback(ch, method, properties, body):
    db = SessionLocal()
    try:
        payload = json.loads(body)
        _process_message(db, payload)
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception:
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    finally:
        db.close()


def start_worker() -> None:
    connection = get_connection()
    channel = connection.channel()
    ensure_topology(channel)
    channel.basic_qos(prefetch_count=settings.rabbitmq_prefetch)

    channel.basic_consume(queue=settings.rabbitmq_queue, on_message_callback=callback, auto_ack=False)
    channel.start_consuming()


if __name__ == "__main__":
    while True:
        try:
            start_worker()
        except pika.exceptions.AMQPConnectionError:
            time.sleep(3)
