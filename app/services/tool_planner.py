from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolPlan:
    intent: str
    required_entities: list[str]
    tools: list[str]
    analysis_path: list[str]
    entities: dict[str, Any] = field(default_factory=dict)


def build_tool_plan(intent: str, entities: dict[str, Any]) -> ToolPlan:
    """Build an explainable read-only tool plan for supported intents."""
    if intent == "order_delivery_risk":
        return ToolPlan(
            intent=intent,
            required_entities=["order_no"],
            tools=[
                "analyze_order_delivery_risk",
                "query_order_status",
                "query_inventory_by_sku",
                "query_purchase_arrival",
                "query_exception_sop",
            ],
            analysis_path=[
                "identify_order",
                "query_order_status",
                "query_inventory",
                "query_purchase_arrival",
                "query_exception_sop",
                "compose_answer",
            ],
            entities=entities,
        )
    if intent == "work_order_readiness":
        return ToolPlan(
            intent=intent,
            required_entities=["work_order_no"],
            tools=[
                "analyze_work_order_readiness",
                "query_work_order",
                "query_inventory_by_sku",
                "query_exception_sop",
            ],
            analysis_path=[
                "identify_work_order",
                "query_work_order",
                "query_material_inventory",
                "query_exception_sop",
                "compose_answer",
            ],
            entities=entities,
        )
    if intent == "purchase_delay_impact":
        return ToolPlan(
            intent=intent,
            required_entities=["purchase_order_no"],
            tools=[
                "analyze_purchase_delay_impact",
                "query_purchase_arrival",
                "query_order_status",
                "query_exception_sop",
            ],
            analysis_path=[
                "identify_purchase_order",
                "query_purchase_arrival",
                "query_affected_orders",
                "query_exception_sop",
                "compose_answer",
            ],
            entities=entities,
        )
    if intent == "inventory_batches":
        return ToolPlan(
            intent=intent,
            required_entities=["sku_code"],
            tools=["query_inventory_by_sku"],
            analysis_path=["identify_sku", "query_inventory_batches", "compose_answer"],
            entities=entities,
        )
    return ToolPlan(
        intent=intent,
        required_entities=[],
        tools=["query_exception_sop"],
        analysis_path=["identify_exception_question", "query_exception_sop", "compose_answer"],
        entities=entities,
    )


def missing_entities(plan: ToolPlan) -> list[str]:
    return [name for name in plan.required_entities if not plan.entities.get(name)]
