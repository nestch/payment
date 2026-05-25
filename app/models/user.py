from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class User(Base):
    __tablename__ = "userTable"

    id: Mapped[int] = mapped_column("userID", Integer, primary_key=True, autoincrement=True)
    name: Mapped[str | None] = mapped_column("name", String(100), nullable=True)
    email: Mapped[str] = mapped_column("email", String(255), nullable=False, unique=True, index=True)
    created_at: Mapped[int | None] = mapped_column("createdAt", Integer, nullable=True)
    updated_at: Mapped[int | None] = mapped_column("updatedAt", Integer, nullable=True)
