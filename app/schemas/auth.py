from datetime import datetime

from pydantic import BaseModel, Field


class TokenCreateRequest(BaseModel):
    userID: int | None = Field(default=None, gt=0)
    expires_in_minutes: int | None = Field(default=None, gt=0, le=60 * 24 * 7)


class TokenCreateResponse(BaseModel):
    access_token: str
    token_type: str
    expires_at: datetime
