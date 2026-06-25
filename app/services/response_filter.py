from copy import deepcopy
from typing import Any

from app.core.permissions import Role
from app.schemas import AnalysisResponse, ChatResponse, ToolResponse


SENSITIVE_FIELDS = {
    "supplier_price",
    "purchase_price",
    "cost",
    "inventory_cost",
    "sales_amount",
    "internal_remark",
    "internal_note",
    "supplier_internal_info",
    "customer_contact",
    "customer_phone",
    "customer_address",
}

ROLE_BLOCKED_FIELDS: dict[str, set[str]] = {
    Role.ADMIN: set(),
    Role.NORMAL_USER: SENSITIVE_FIELDS
    | {
        "customer_name",
        "supplier_name",
        "order_status",
        "delivery_status",
        "planned_delivery_date",
        "items",
        "batches",
        "materials",
        "total_quantity",
        "available_quantity",
        "locked_quantity",
        "quality_hold_quantity",
    },
    Role.SALES: {
        "supplier_price",
        "purchase_price",
        "cost",
        "inventory_cost",
        "supplier_internal_info",
        "internal_remark",
        "internal_note",
    },
    Role.WAREHOUSE: {
        "customer_name",
        "customer_contact",
        "customer_phone",
        "customer_address",
        "sales_amount",
        "supplier_price",
        "purchase_price",
        "cost",
    },
    Role.PURCHASE: {
        "customer_contact",
        "customer_phone",
        "customer_address",
        "sales_amount",
        "internal_remark",
        "internal_note",
    },
    Role.PRODUCTION_MANAGER: {
        "purchase_price",
        "supplier_price",
        "customer_contact",
        "customer_phone",
        "customer_address",
    },
}


def _filter_value(value: Any, blocked_fields: set[str]) -> tuple[Any, bool]:
    if isinstance(value, dict):
        changed = False
        filtered: dict[str, Any] = {}
        for key, item in value.items():
            if key in blocked_fields:
                changed = True
                continue
            filtered_item, item_changed = _filter_value(item, blocked_fields)
            filtered[key] = filtered_item
            changed = changed or item_changed
        return filtered, changed

    if isinstance(value, list):
        changed = False
        filtered_list = []
        for item in value:
            filtered_item, item_changed = _filter_value(item, blocked_fields)
            filtered_list.append(filtered_item)
            changed = changed or item_changed
        return filtered_list, changed

    return value, False


def filter_response_by_role(
    data: dict[str, Any],
    user_role: str,
    resource_type: str = "business",
) -> tuple[dict[str, Any], bool]:
    if user_role == Role.ADMIN:
        return deepcopy(data), False
    if resource_type == "sop":
        blocked_fields = SENSITIVE_FIELDS
    else:
        blocked_fields = ROLE_BLOCKED_FIELDS.get(user_role, SENSITIVE_FIELDS)
    filtered, changed = _filter_value(deepcopy(data), blocked_fields)
    return filtered, changed


def filter_tool_response(response: ToolResponse, user_role: str) -> tuple[ToolResponse, bool]:
    if not isinstance(response.data, dict):
        return response, False
    resource_type = "sop" if response.tool_name == "query_exception_sop" else "business"
    filtered_data, changed = filter_response_by_role(response.data, user_role, resource_type)
    return response.model_copy(update={"data": filtered_data}), changed


def filter_analysis_response(
    response: AnalysisResponse,
    user_role: str,
) -> tuple[AnalysisResponse, bool]:
    changed = False
    called_tools: list[ToolResponse] = []
    for tool in response.called_tools:
        filtered_tool, tool_changed = filter_tool_response(tool, user_role)
        called_tools.append(filtered_tool)
        changed = changed or tool_changed
    return response.model_copy(update={"called_tools": called_tools}), changed


def filter_chat_response(response: ChatResponse, user_role: str) -> ChatResponse:
    changed = False
    called_tools: list[ToolResponse] = []
    for tool in response.called_tools:
        filtered_tool, tool_changed = filter_tool_response(tool, user_role)
        called_tools.append(filtered_tool)
        changed = changed or tool_changed

    if not changed:
        return response.model_copy(update={"called_tools": called_tools})

    trace = list(response.execution_trace)
    trace.append(
        {
            "step": "response_filter",
            "status": "applied",
            "detail": f"Applied field-level filtering for role={user_role}",
        }
    )
    return response.model_copy(update={"called_tools": called_tools, "execution_trace": trace})
