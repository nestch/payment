import enum
import datetime as dt

from sqlalchemy import BigInteger, Date, Enum, ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class UserPackageStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


class UserPackage(Base):
    __tablename__ = "user_packages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    package_id: Mapped[int] = mapped_column(ForeignKey("payment_packages.id"), nullable=False, index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("payments.id"), nullable=False, index=True)

    start_date: Mapped[dt.date] = mapped_column(Date, nullable=False)
    end_date: Mapped[dt.date] = mapped_column(Date, nullable=False)

    status: Mapped[UserPackageStatus] = mapped_column(
        Enum(UserPackageStatus),
        nullable=False,
        default=UserPackageStatus.ACTIVE,
    )


Index("ix_user_packages_user_payment", UserPackage.user_id, UserPackage.payment_id)
