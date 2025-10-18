from datetime import UTC, datetime
from typing import Any, ClassVar

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.lib.enums import UserRole


def now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[type, Any]] = {
        datetime: DateTime(timezone=True),
    }


class Users(Base):
    __tablename__: str = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(default=False)

    sessions: Mapped[list["Sessions"]] = relationship("Sessions", back_populates="user")


class Sessions(Base):
    __tablename__: str = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(default=now)
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    revoked: Mapped[bool] = mapped_column(default=False)

    user: Mapped["Users"] = relationship("Users", back_populates="sessions")
