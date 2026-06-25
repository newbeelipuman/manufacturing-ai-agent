from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import InventorySku
from app.models.order import SalesOrder, SalesOrderItem
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.work_order import WorkOrder


def _number(value: Any) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value or 0)


def _date(value: Any) -> str | None:
    if isinstance(value, date):
        return value.isoformat()
    return None


def _status_label(value: Any) -> str:
    labels = {
        "confirmed": "已确认",
        "pending": "待处理",
        "planned": "已计划",
        "delayed": "延期",
        "completed": "已完成",
        "closed": "已关闭",
        "open": "未关闭",
    }
    text = str(value or "未知")
    return labels.get(text, text)


def analyze_shipment_risk(db: Session, order_no: str) -> dict[str, Any]:
    """Calculate read-only shipment feasibility from simulated data."""
    order = db.scalar(select(SalesOrder).where(SalesOrder.order_no == order_no))
    if not order:
        return {
            "found": False,
            "order_no": order_no,
            "can_ship": False,
            "partial_ship": False,
            "shortage_risk": "unknown",
            "delivery_delay_risk": "unknown",
            "manual_review_required": True,
            "risk_level": "unknown",
            "risk_factors": ["business_identifier_not_found"],
            "manual_review_reason": ["business_identifier_not_found"],
            "evidence": [f"未找到销售订单 {order_no}。"],
            "recommendations": ["请核对销售订单号后重试。"],
        }

    items = db.scalars(
        select(SalesOrderItem).where(SalesOrderItem.order_no == order_no)
    ).all()
    evidence: list[str] = [
        (
            f"订单 {order_no}：订单状态 {_status_label(order.order_status)}，"
            f"发货状态 {_status_label(order.delivery_status)}，"
            f"计划交付日期 {order.planned_delivery_date}。"
        )
    ]
    recommendations: list[str] = []
    shortages: list[dict[str, Any]] = []
    has_partial = False
    has_quality_hold = False
    has_delayed_purchase = False
    has_replenishment = False

    for item in items:
        demand = _number(item.quantity) - _number(item.delivered_quantity)
        inventory = db.scalar(select(InventorySku).where(InventorySku.sku_code == item.sku_code))
        available = _number(inventory.available_quantity) if inventory else 0
        locked = _number(inventory.locked_quantity) if inventory else 0
        quality_hold = _number(inventory.quality_hold_quantity) if inventory else 0
        usable = max(available - quality_hold, 0)
        short = max(demand - usable, 0)
        if quality_hold > 0:
            has_quality_hold = True
        if usable > 0 and short > 0:
            has_partial = True
        if short > 0:
            shortages.append(
                {
                    "sku_code": item.sku_code,
                    "demand": demand,
                    "usable_inventory": usable,
                    "shortage_quantity": short,
                }
            )
        evidence.append(
            (
                f"{item.sku_code}：需求 {demand:g}，可用库存 {available:g}，"
                f"锁定库存 {locked:g}，质量冻结 {quality_hold:g}，"
                f"可承诺发货量 {usable:g}，缺口 {short:g}。"
            )
        )

        purchase_items = db.scalars(
            select(PurchaseOrderItem).where(PurchaseOrderItem.sku_code == item.sku_code)
        ).all()
        for purchase_item in purchase_items:
            purchase = db.scalar(
                select(PurchaseOrder).where(
                    PurchaseOrder.purchase_order_no == purchase_item.purchase_order_no
                )
            )
            if purchase:
                has_delayed_purchase = has_delayed_purchase or bool(purchase.is_delayed)
                evidence.append(
                    (
                        f"采购单 {purchase.purchase_order_no}：状态 {_status_label(purchase.status)}，"
                        f"预计到货 {purchase.expected_arrival_date}，"
                        f"是否延期 {'是' if purchase.is_delayed else '否'}，"
                        f"未到货数量 {_number(purchase_item.quantity) - _number(purchase_item.arrived_quantity):g}。"
                    )
                )

        work_orders = db.scalars(
            select(WorkOrder).where(WorkOrder.product_sku == item.sku_code)
        ).all()
        for work_order in work_orders:
            open_qty = max(
                _number(work_order.planned_quantity) - _number(work_order.finished_quantity),
                0,
            )
            if open_qty > 0:
                has_replenishment = True
                evidence.append(
                    (
                        f"工单 {work_order.work_order_no}：状态 {_status_label(work_order.status)}，"
                        f"未完工数量 {open_qty:g}，"
                        f"预计补货日期 {_date(work_order.expected_replenishment_date)}。"
                    )
                )

    can_ship = bool(items) and not shortages
    partial_ship = bool(shortages) and has_partial
    shortage_risk = "high" if shortages else "low"
    delivery_delay_risk = "high" if shortages and has_delayed_purchase else "medium" if shortages else "low"
    manual_review_required = bool(shortages or has_quality_hold or has_delayed_purchase)
    if shortages and has_delayed_purchase:
        risk_level = "high"
    elif shortages or has_quality_hold:
        risk_level = "medium"
    else:
        risk_level = "low"

    if shortages:
        shortage_text = "; ".join(
            f"{row['sku_code']} 缺口 {row['shortage_quantity']:g}" for row in shortages
        )
        recommendations.append(f"暂不自动发货，先人工复核物料缺口：{shortage_text}。")
    if has_quality_hold:
        recommendations.append("质量负责人需先复核冻结库存，再确认是否承诺发货。")
    if has_delayed_purchase:
        recommendations.append("采购确认延期到货时间，销售同步客户交期风险。")
    if has_replenishment:
        recommendations.append("生产确认工单补货节奏，再更新承诺交付日期。")
    if not recommendations:
        recommendations.append("库存初步满足需求，仍需仓库和业务负责人确认后再发货。")

    risk_factors: list[str] = []
    manual_review_reason: list[str] = []
    if shortages:
        risk_factors.append("inventory_shortage")
        manual_review_reason.append("inventory_shortage")
    if has_quality_hold:
        risk_factors.append("quality_hold")
        manual_review_reason.append("quality_hold")
    if has_delayed_purchase:
        risk_factors.append("purchase_delay")
        manual_review_reason.append("purchase_delay")
    if has_replenishment:
        risk_factors.append("work_order_replenishment")

    return {
        "found": True,
        "order_no": order_no,
        "can_ship": can_ship,
        "partial_ship": partial_ship,
        "shortage_risk": shortage_risk,
        "delivery_delay_risk": delivery_delay_risk,
        "manual_review_required": manual_review_required,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "manual_review_reason": manual_review_reason,
        "shortages": shortages,
        "evidence": evidence,
        "recommendations": recommendations,
    }
