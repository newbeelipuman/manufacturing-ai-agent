from typing import Any

from app.schemas import ToolResponse


INTENT_LABELS = {
    "order_delivery_risk": "订单发货风险分析",
    "work_order_readiness": "工单开工齐套分析",
    "purchase_delay_impact": "采购延期影响分析",
    "inventory_batches": "库存批次查询",
    "exception_sop": "制造异常 SOP 检索",
    "clarify_order_delivery_risk": "补充订单号",
    "clarify_work_order_readiness": "补充工单号",
    "clarify_purchase_delay_impact": "补充采购单号",
    "clarify_inventory_batches": "补充 SKU 编码",
}

ENTITY_LABELS = {
    "order_no": "订单号",
    "work_order_no": "工单号",
    "purchase_order_no": "采购单号",
    "sku_code": "SKU 编码",
    "business identifier": "业务编号",
}

ENTITY_EXAMPLES = {
    "order_no": "O1001",
    "work_order_no": "WO1001",
    "purchase_order_no": "PO1001",
    "sku_code": "SKU-KB-001",
    "business identifier": "O1001、WO1001、PO1001 或 SKU-KB-001",
}

CLARIFY_ENTITY_BY_INTENT = {
    "clarify_order_delivery_risk": "order_no",
    "clarify_work_order_readiness": "work_order_no",
    "clarify_purchase_delay_impact": "purchase_order_no",
    "clarify_inventory_batches": "sku_code",
}


def manual_reminder() -> str:
    return "涉及发货、调账、审批、下单等高风险业务动作时，必须由人在企业系统中确认后执行。"


def compose_answer(
    intent: str,
    analysis_path: list[str],
    checked_data: list[str],
    called_tools: list[ToolResponse],
    business_conclusion: str,
    suggested_next_action: str,
) -> str:
    """Compose the required audit-friendly answer shape."""
    tools = " | ".join(
        f"{tool.tool_name}({'allowed' if tool.permission_allowed else 'denied'})"
        for tool in called_tools
    )
    display_intent = INTENT_LABELS.get(intent, intent)
    return (
        f"路由意图: {display_intent} ({intent})\n"
        f"分析路径: {' -> '.join(analysis_path)}\n"
        f"检查数据: {' | '.join(checked_data)}\n"
        f"调用工具: {tools or 'none'}\n"
        f"业务结论: {business_conclusion}\n"
        f"建议下一步: {suggested_next_action}\n"
        f"人工确认: {manual_reminder()}"
    )


def compose_clarification(
    intent: str,
    missing: list[str],
    entities: dict[str, Any],
) -> tuple[str, str, str]:
    if missing == ["business identifier"] and intent in CLARIFY_ENTITY_BY_INTENT:
        missing = [CLARIFY_ENTITY_BY_INTENT[intent]]
    labels = [ENTITY_LABELS.get(item, item) for item in missing]
    examples = [ENTITY_EXAMPLES.get(item) for item in missing if ENTITY_EXAMPLES.get(item)]
    missing_text = "、".join(labels)
    example_text = "、".join(examples) if examples else "O1001"
    display_intent = INTENT_LABELS.get(intent, intent)
    conclusion = f"我还不能直接查询，因为问题里缺少{missing_text}。目前没有调用业务工具。"
    action = f"请补充{missing_text}后再试，例如：{example_text}。"
    answer = (
        f"路由意图: {display_intent}\n"
        f"识别实体: {entities or '未识别到关键业务编号'}\n"
        f"业务结论: {conclusion}\n"
        f"建议下一步: {action}\n"
        f"人工确认: {manual_reminder()}"
    )
    return answer, conclusion, action
