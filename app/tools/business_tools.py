from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventoryBatch, InventorySku
from app.models.order import SalesOrder, SalesOrderItem
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.work_order import WorkOrder, WorkOrderMaterial
from app.rag.retriever import search_sop_chunks


def _value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def query_order_status(db: Session, order_no: str) -> dict[str, Any]:
    """Read sales order header and line status for a simulated order."""
    order = db.scalar(select(SalesOrder).where(SalesOrder.order_no == order_no))
    if not order:
        return {"found": False, "order_no": order_no}

    items = db.scalars(
        select(SalesOrderItem).where(SalesOrderItem.order_no == order_no)
    ).all()
    return {
        "found": True,
        "order_no": order.order_no,
        "customer_name": order.customer_name,
        "order_status": order.order_status,
        "delivery_status": order.delivery_status,
        "planned_delivery_date": _value(order.planned_delivery_date),
        "items": [
            {
                "sku_code": item.sku_code,
                "sku_name": item.sku_name,
                "quantity": _value(item.quantity),
                "delivered_quantity": _value(item.delivered_quantity),
                "locked_quantity": _value(item.locked_quantity),
            }
            for item in items
        ],
    }


def query_inventory_by_sku(db: Session, sku_code: str) -> dict[str, Any]:
    """Read available, locked, and batch inventory for one SKU."""
    sku = db.scalar(select(InventorySku).where(InventorySku.sku_code == sku_code))
    batches = db.scalars(
        select(InventoryBatch).where(InventoryBatch.sku_code == sku_code)
    ).all()
    if not sku:
        return {"found": False, "sku_code": sku_code, "batches": []}

    return {
        "found": True,
        "sku_code": sku.sku_code,
        "sku_name": sku.sku_name,
        "total_quantity": _value(sku.total_quantity),
        "available_quantity": _value(sku.available_quantity),
        "locked_quantity": _value(sku.locked_quantity),
        "quality_hold_quantity": _value(sku.quality_hold_quantity),
        "unit": sku.unit,
        "batches": [
            {
                "batch_no": batch.batch_no,
                "warehouse_code": batch.warehouse_code,
                "quantity": _value(batch.quantity),
                "available_quantity": _value(batch.available_quantity),
                "locked_quantity": _value(batch.locked_quantity),
                "quality_hold_quantity": _value(batch.quality_hold_quantity),
                "production_date": _value(batch.production_date),
                "expire_date": _value(batch.expire_date),
            }
            for batch in batches
        ],
    }


def query_work_order(db: Session, work_order_no: str) -> dict[str, Any]:
    """Read work order plan and required materials."""
    work_order = db.scalar(
        select(WorkOrder).where(WorkOrder.work_order_no == work_order_no)
    )
    if not work_order:
        return {"found": False, "work_order_no": work_order_no}

    materials = db.scalars(
        select(WorkOrderMaterial).where(
            WorkOrderMaterial.work_order_no == work_order_no
        )
    ).all()
    return {
        "found": True,
        "work_order_no": work_order.work_order_no,
        "product_sku": work_order.product_sku,
        "product_name": work_order.product_name,
        "planned_quantity": _value(work_order.planned_quantity),
        "finished_quantity": _value(work_order.finished_quantity),
        "status": work_order.status,
        "planned_start_date": _value(work_order.planned_start_date),
        "planned_end_date": _value(work_order.planned_end_date),
        "expected_replenishment_date": _value(work_order.expected_replenishment_date),
        "materials": [
            {
                "material_sku": material.material_sku,
                "material_name": material.material_name,
                "required_quantity": _value(material.required_quantity),
                "issued_quantity": _value(material.issued_quantity),
            }
            for material in materials
        ],
    }


def query_purchase_arrival(db: Session, purchase_order_no: str) -> dict[str, Any]:
    """Read purchase order arrival plan and item quantities."""
    purchase_order = db.scalar(
        select(PurchaseOrder).where(
            PurchaseOrder.purchase_order_no == purchase_order_no
        )
    )
    if not purchase_order:
        return {"found": False, "purchase_order_no": purchase_order_no}

    items = db.scalars(
        select(PurchaseOrderItem).where(
            PurchaseOrderItem.purchase_order_no == purchase_order_no
        )
    ).all()
    return {
        "found": True,
        "purchase_order_no": purchase_order.purchase_order_no,
        "supplier_name": purchase_order.supplier_name,
        "status": purchase_order.status,
        "expected_arrival_date": _value(purchase_order.expected_arrival_date),
        "is_delayed": purchase_order.is_delayed,
        "items": [
            {
                "sku_code": item.sku_code,
                "sku_name": item.sku_name,
                "quantity": _value(item.quantity),
                "arrived_quantity": _value(item.arrived_quantity),
            }
            for item in items
        ],
    }


def query_exception_sop(db: Session, question: str) -> dict[str, Any]:
    """Read matching SOP knowledge chunks with local scored retrieval."""
    results = search_sop_chunks(db=db, query=question, limit=5)
    return {"found": bool(results), "query": question, "results": results}
