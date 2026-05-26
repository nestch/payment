from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings
from app.schemas.auth import TokenCreateRequest, TokenCreateResponse
from app.services.zavu_service import _send_whatsapp


router = APIRouter(prefix="/auth", tags=["auth"])


class ZavuTestRequest(BaseModel):
    phone: str
    message: str = "Teste de mensagem Zavu"


class ZavuTestResponse(BaseModel):
    success: bool
    message: str


@router.post("/test-zavu", response_model=ZavuTestResponse)
def test_zavu(req: ZavuTestRequest):
    try:
        _send_whatsapp(req.phone, req.message)
        return ZavuTestResponse(success=True, message=f"Mensagem enviada para {req.phone}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar: {str(e)}")


@router.post("/token", response_model=TokenCreateResponse)
def create_token(req: TokenCreateRequest):
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=req.expires_in_minutes)

    payload: dict = {"exp": int(expires_at.timestamp())}
    if req.user_id is not None:
        payload["user_id"] = req.user_id
        payload["sub"] = str(req.user_id)

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return TokenCreateResponse(access_token=token, token_type="bearer", expires_at=expires_at)
