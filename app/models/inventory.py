from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class InventorySku(Base):
    __tablename__ = "inventory_sku"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku_code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    sku_name: Mapped[str] = mapped_column(String(128))
    total_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    locked_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    quality_hold_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    unit: Mapped[str] = mapped_column(String(16))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InventoryBatch(Base):
    __tablename__ = "inventory_batch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    batch_no: Mapped[str] = mapped_column(String(64), index=True)
    warehouse_code: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    available_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    locked_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    quality_hold_quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    production_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class InventoryTransaction(Base):
    __tablename__ = "inventory_transaction"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sku_code: Mapped[str] = mapped_column(String(64), index=True)
    batch_no: Mapped[str] = mapped_column(String(64), index=True)
    transaction_type: Mapped[str] = mapped_column(String(32), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    source_doc_no: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
