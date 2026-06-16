from decimal import Decimal

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import text
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
    # O Stripe envia a assinatura do webhook nesse header. Sem ele não dá pra validar autenticidade.
    if stripe_signature is None:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    # Corpo bruto do request (necessário para validação da assinatura)
    payload = await request.body()

    try:
        # Valida a assinatura do webhook usando STRIPE_WEBHOOK_SECRET.
        # Se a assinatura não bater, rejeitamos com 400.
        event = construct_webhook_event(payload=payload, stripe_signature=stripe_signature)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid webhook signature") from exc

    # O SDK do Stripe devolve um StripeObject (não é dict puro). Convertendo para dict para acessar
    # com .get(...) sem quebrar. Algumas versões expõem métodos diferentes, então tratamos os 3 casos.
    if hasattr(event, "to_dict_recursive"):
        event_dict = event.to_dict_recursive()
    elif hasattr(event, "_to_dict_recursive"):
        event_dict = event._to_dict_recursive()
    else:
        event_dict = event.to_dict()

    # Tipo do evento (ex.: checkout.session.completed)
    event_type = event_dict.get("type")
    # Objeto principal do evento (varia por tipo: checkout.session, payment_intent, charge, etc.)
    obj = (event_dict.get("data") or {}).get("object") or {}
    # Metadata que definimos ao criar a sessão/intent (melhor lugar para carregar nosso payment_id)
    metadata = obj.get("metadata") or {}

    # Tentamos descobrir qual Payment interno esse evento se refere.
    # Ao criar a sessão no Checkout, salvamos payment_id no metadata e também setamos client_reference_id.
    payment_id = metadata.get("payment_id")
    if payment_id is None and obj.get("client_reference_id"):
        payment_id = obj.get("client_reference_id")

    # Se não acharmos payment_id, não temos o que atualizar no nosso banco.
    # Retornamos 200 para o Stripe não ficar re-tentando sem necessidade.
    if payment_id is None:
        return {"received": True}

    # O payment_id no metadata precisa ser um número.
    # Se vier algo inválido, também respondemos 200 e ignoramos.
    try:
        payment_id_int = int(payment_id)
    except (TypeError, ValueError):
        return {"received": True}

    # Busca o Payment no nosso banco local
    payment: Payment | None = db.query(Payment).filter(Payment.id == payment_id_int).one_or_none()
    if payment is None:
        return {"received": True}

    # Atualiza status de acordo com o tipo do evento
    if event_type == "checkout.session.completed":
        # Checkout finalizado com sucesso -> pagamento confirmado
        payment.status = PaymentStatus.CONFIRMED
        if obj.get("payment_intent"):
            # Se existir, guardamos o PaymentIntent do Stripe para rastreio
            payment.transaction_id = obj.get("payment_intent")

        # Atualiza o crédito do usuário no banco principal (nestch_db).
        # Premissa: userTable.credit é DOUBLE (numérico com casas decimais).
        credits_str = str(payment.credits) if payment.credits is not None else metadata.get("credits")
        try:
            credits_val = Decimal(credits_str) if credits_str is not None else Decimal("0")
        except Exception:
            credits_val = Decimal("0")

        # Idempotência: o Stripe pode reenviar eventos; creditamos apenas uma vez por Payment.
        if credits_val > 0 and payment.credited_at is None:
            db.execute(
                text(
                    "INSERT IGNORE INTO creditsLedger (userID, payment_id, credits, amount_paid, stripe_event_id) "
                    "VALUES (:userID, :payment_id, :credits, :amount_paid, :stripe_event_id)"
                ),
                {
                    "userID": payment.userID,
                    "payment_id": payment.id,
                    "credits": credits_val,
                    "amount_paid": payment.amount,
                    "stripe_event_id": event_dict.get("id"),
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

    elif event_type in {"checkout.session.async_payment_failed", "payment_intent.payment_failed"}:
        # Falha no pagamento
        payment.status = PaymentStatus.FAILED

    elif event_type in {"checkout.session.expired"}:
        # Sessão expirada (usuário não concluiu)
        payment.status = PaymentStatus.CANCELED

    # Persiste a alteração
    db.add(payment)
    db.commit()

    # Sempre responder 200 para o Stripe considerar o evento entregue
    return {"received": True}
