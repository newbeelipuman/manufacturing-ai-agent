from typing import Any


def detect_intent(question: str, entities: dict[str, Any]) -> str:
    """Classify the supported P1 demo intents with deterministic rules."""
    if entities.get("purchase_order_no"):
        return "purchase_delay_impact"
    if entities.get("work_order_no"):
        return "work_order_readiness"
    if entities.get("order_no"):
        return "order_delivery_risk"
    if entities.get("sku_code"):
        return "inventory_batches"

    if any(term in question for term in ["订单"]) and any(term in question for term in ["发货"]):
        return "clarify_order_delivery_risk"
    if any(term in question for term in ["工单"]):
        return "clarify_work_order_readiness"
    if any(term in question for term in ["采购单"]):
        return "clarify_purchase_delay_impact"
    if any(term in question for term in ["库存", "批次"]):
        return "clarify_inventory_batches"
    return "exception_sop"
