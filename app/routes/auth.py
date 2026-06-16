import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter

from app.schemas.auth import TokenCreateRequest, TokenCreateResponse

load_dotenv()

_JWT_SECRET: str = os.getenv("JWT_KEY", "nestch")
_JWT_ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=TokenCreateResponse)
def create_token(req: TokenCreateRequest):
    expire_minutes = req.expires_in_minutes
    expires_at = datetime.now(tz=timezone.utc) + timedelta(minutes=expire_minutes)

    payload: dict = {"exp": int(expires_at.timestamp())}
    if req.userID is not None:
        payload["userID"] = req.userID
        payload["sub"] = str(req.userID)

    token = jwt.encode(payload, _JWT_SECRET, algorithm=_JWT_ALGORITHM)

    return TokenCreateResponse(access_token=token, token_type="bearer", expires_at=expires_at)
