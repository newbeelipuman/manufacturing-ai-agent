from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SalesOrder(Base):
    __tablename__ = "sales_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_name: Mapped[str] = mapped_column(String(128))
    order_status: Mapped[str] = mapped_column(String(32), index=True)
    delivery_status: Mapped[str] = mapped_column(String(32), index=True)
    planned_delivery_date: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class SalesOrderItem(Base):
    __tablename__ = "sales_order_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_no: Mapped[str] = mapped_column(String(64), index=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    sku_name: Mapped[str] = mapped_column(String(128))
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    delivered_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    locked_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
