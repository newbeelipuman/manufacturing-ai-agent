from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PermissionRequest(Base):
    __tablename__ = "permission_request"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    requester_username: Mapped[str] = mapped_column(String(64), index=True)
    requested_permission: Mapped[str] = mapped_column(String(128), index=True)
    requested_role: Mapped[str | None] = mapped_column(String(64), nullable=True)
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    approver_username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    approval_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
