from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PermissionChangeLog(Base):
    __tablename__ = "permission_change_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[str] = mapped_column(String(32), index=True)
    operator_username: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(32), index=True)
    target_identifier: Mapped[str] = mapped_column(String(128), index=True)
    permission_code: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    before_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    after_value: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    diff: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    remark: Mapped[str] = mapped_column(Text)
    request_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
