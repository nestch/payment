from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.db_nestch import get_nestch_db_session


_bearer = HTTPBearer(auto_error=False)


def require_auth(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> dict:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expired") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Invalid token") from exc

    return payload


def require_active_user(
    payload: dict = Depends(require_auth),
    db: Session = Depends(get_nestch_db_session),
) -> dict:
    userID = payload.get("userID")
    if userID is None:
        raise HTTPException(status_code=401, detail="Token missing userID")

    from app.models.user import User

    user = (
        db.query(User)
        .filter(User.id == userID, User.userStatus == 1)
        .one_or_none()
    )
    if user is None:
        raise HTTPException(status_code=403, detail="User not found or inactive")

    return payload
