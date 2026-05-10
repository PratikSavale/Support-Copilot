from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import TimestampedModel
from models.enums import UserRole

if TYPE_CHECKING:
    from models.session import Session


class User(TimestampedModel):
    __tablename__ = "users"

    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        SAEnum(UserRole, native_enum=False, length=20),
        default=UserRole.agent,
        nullable=False,
    )

    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
