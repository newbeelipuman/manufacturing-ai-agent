from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    supplier_name: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(32), index=True)
    expected_arrival_date: Mapped[date] = mapped_column(Date)
    is_delayed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    purchase_order_no: Mapped[str] = mapped_column(String(64), index=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    sku_name: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    arrived_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
