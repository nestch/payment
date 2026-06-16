import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db_session
from app.models.payment import Payment
from app.schemas.payments import (
    SimulateCallbackRequest,
    SimulateCallbackResponse,
    SimulateCheckoutRequest,
    SimulateCheckoutResponse,
)
from app.security.jwt import require_auth
from app.services.simulate_service import (
    cancel_simulated_payment,
    confirm_simulated_payment,
    create_simulated_payment,
    fail_simulated_payment,
)


_logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulate", tags=["simulate"])

_OUTCOME_EVENT = {
    "success": "checkout.session.completed",
    "failure": "checkout.session.async_payment_failed",
    "cancel": "checkout.session.expired",
}


def _apply_outcome(db: Session, payment: Payment, simulate: str) -> None:
    if simulate == "success":
        confirm_simulated_payment(db, payment)
    elif simulate == "failure":
        fail_simulated_payment(db, payment)
    else:
        cancel_simulated_payment(db, payment)


@router.post("/checkout", response_model=SimulateCheckoutResponse)
def simulate_checkout(
    req: SimulateCheckoutRequest,
    _payload: dict = Depends(require_auth),
    db: Session = Depends(get_db_session),
):
    """
    Cria um Payment (PIX, PENDING) e imediatamente simula o desfecho do pagamento.
    - simulate='success'  → status CONFIRMED + creditsLedger alimentado
    - simulate='failure'  → status FAILED
    - simulate='cancel'   → status CANCELED
    """
    try:
        payment = create_simulated_payment(
            db,
            user_id=req.user_id,
            credits=req.credits,
            currency=req.currency,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    _apply_outcome(db, payment, req.simulate)
    db.refresh(payment)

    return SimulateCheckoutResponse(
        payment_id=payment.id,
        status=payment.status.value,
        simulated_event=_OUTCOME_EVENT[req.simulate],
        transaction_id=payment.transaction_id,
    )


@router.post("/callback", response_model=SimulateCallbackResponse)
def simulate_callback(
    req: SimulateCallbackRequest,
    _payload: dict = Depends(require_auth),
    db: Session = Depends(get_db_session),
):
    """
    Aplica um desfecho simulado sobre um Payment já existente (PENDING).
    Útil para simular a progressão de status em etapas separadas:
      1. POST /simulate/checkout  → cria PENDING
      2. POST /simulate/callback  → confirma/falha/cancela
    """
    payment: Payment | None = db.query(Payment).filter(Payment.id == req.payment_id).one_or_none()
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    if payment.status.value != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Payment already in terminal status: {payment.status.value}",
        )

    _apply_outcome(db, payment, req.simulate)
    db.refresh(payment)

    return SimulateCallbackResponse(
        payment_id=payment.id,
        status=payment.status.value,
        simulated_event=_OUTCOME_EVENT[req.simulate],
    )
