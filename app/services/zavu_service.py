import logging
from decimal import Decimal

import httpx

from app.config import settings

_logger = logging.getLogger(__name__)

_ZAVU_API_URL = "https://api.zavu.dev/v1/messages"


def _send_whatsapp(to: str, text: str) -> None:
    if not settings.zavu_enabled:
        return

    if not settings.zavu_api_key:
        _logger.warning("ZAVU_API_KEY not configured, skipping WhatsApp notification")
        return

    try:
        response = httpx.post(
            _ZAVU_API_URL,
            json={"to": to, "channel": "whatsapp", "text": text},
            headers={"Authorization": f"Bearer {settings.zavu_api_key}"},
            timeout=10,
        )
        response.raise_for_status()
    except Exception:
        _logger.exception("Failed to send WhatsApp notification to %s", to)


def notify_payment_confirmed(payment_id: int, amount: Decimal, currency: str) -> None:
    text = (
        f"✅ Pagamento confirmado!\n"
        f"ID: {payment_id}\n"
        f"Valor: {currency.upper()} {amount:.2f}"
    )
    for number in settings.zavu_notify_numbers_list:
        _send_whatsapp(number, text)


def notify_payment_failed(payment_id: int) -> None:
    text = f"❌ Pagamento falhou!\nID: {payment_id}"
    for number in settings.zavu_notify_numbers_list:
        _send_whatsapp(number, text)
