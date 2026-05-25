from datetime import datetime, timedelta, timezone

import jwt
from fastapi import APIRouter

from app.config import settings
from app.schemas.auth import TokenCreateRequest, TokenCreateResponse


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenCreateResponse)
def create_token(req: TokenCreateRequest):
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=req.expires_in_minutes)

    payload: dict = {"exp": int(expires_at.timestamp())}
    if req.user_id is not None:
        payload["user_id"] = req.user_id
        payload["sub"] = str(req.user_id)

    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)

    return TokenCreateResponse(access_token=token, token_type="bearer", expires_at=expires_at)
