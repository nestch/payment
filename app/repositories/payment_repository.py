from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.payment import Payment


class PaymentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, payment_id: int) -> Payment | None:
        return self._db.query(Payment).filter(Payment.id == payment_id).one_or_none()

    def get_by_idempotency_key(self, key: str) -> Payment | None:
        return self._db.query(Payment).filter(Payment.idempotency_key == key).one_or_none()

    def save(self, payment: Payment) -> Payment:
        self._db.add(payment)
        self._db.commit()
        self._db.refresh(payment)
        return payment

    def delete(self, payment: Payment) -> None:
        self._db.delete(payment)
        self._db.commit()
