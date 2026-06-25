from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WorkOrder(Base):
    __tablename__ = "work_order"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_no: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    product_sku: Mapped[str] = mapped_column(String(64), index=True)
    product_name: Mapped[str] = mapped_column(String(128))
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    finished_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    status: Mapped[str] = mapped_column(String(32), index=True)
    planned_start_date: Mapped[date] = mapped_column(Date)
    planned_end_date: Mapped[date] = mapped_column(Date)
    expected_replenishment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class WorkOrderMaterial(Base):
    __tablename__ = "work_order_material"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    work_order_no: Mapped[str] = mapped_column(String(64), index=True)
    material_sku: Mapped[str] = mapped_column(String(64), index=True)
    material_name: Mapped[str] = mapped_column(String(128))
    required_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    issued_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
