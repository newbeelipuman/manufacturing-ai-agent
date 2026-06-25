from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import is_tool_allowed
from app.models.order import SalesOrderItem
from app.schemas import AnalysisResponse, ToolResponse
from app.services.shipment_risk_service import analyze_shipment_risk
from app.services.audit_service import create_tool_call_log
from app.services.tool_service import execute_tool


def _manual_reminder() -> str:
    return "涉及出库、调账、审批、下单、客户承诺等高风险业务动作时，必须由业务人员在企业系统中人工确认执行。"


def _tool_data(called_tools: list[ToolResponse], tool_name: str) -> dict[str, Any]:
    for tool in called_tools:
        if tool.tool_name == tool_name and isinstance(tool.data, dict):
            return tool.data
    return {}


def _all_allowed(called_tools: list[ToolResponse]) -> bool:
    return all(tool.permission_allowed for tool in called_tools)


def _all_success(called_tools: list[ToolResponse]) -> bool:
    return all(tool.success for tool in called_tools)


def _review_fields(
    risk_level: str,
    risk_factors: list[str],
    manual_review_reason: list[str],
) -> dict[str, Any]:
    reasons = list(dict.fromkeys(manual_review_reason))
    if risk_level in {"high", "blocked"} and not reasons:
        reasons.append("clarification_required")
    return {
        "risk_factors": risk_factors,
        "requires_human_review": bool(reasons or risk_level in {"high", "blocked"}),
        "manual_review_reason": reasons,
    }


def _call(
    db: Session,
    username: str,
    role: str,
    agent_call_id: int | None,
    tool_name: str,
    **tool_args: Any,
) -> ToolResponse:
    return execute_tool(
        db=db,
        username=username,
        role=role,
        tool_name=tool_name,
        tool_args=tool_args,
        agent_call_id=agent_call_id,
    )


def _denied_response(
    db: Session,
    username: str,
    role: str,
    analysis_name: str,
    tool_args: dict[str, Any],
    checked_data: list[str],
    agent_call_id: int | None,
) -> AnalysisResponse:
    message = f"角色 {role} 无权调用复合分析 {analysis_name}。"
    create_tool_call_log(
        db=db,
        username=username,
        role=role,
        tool_name=analysis_name,
        tool_args=tool_args,
        permission_allowed=False,
        success=False,
        error_message=message,
        agent_call_id=agent_call_id,
    )
    denied_tool = ToolResponse(
        success=False,
        permission_allowed=False,
        tool_name=analysis_name,
        data=None,
        message=message,
    )
    return AnalysisResponse(
        success=False,
        permission_allowed=False,
        analysis_name=analysis_name,
        checked_data=checked_data,
        called_tools=[denied_tool],
        risk_level="blocked",
        **_review_fields("blocked", ["permission_denied"], ["permission_denied"]),
        business_conclusion=message,
        suggested_next_action="请切换到有权限的业务角色，或仅查询公开 SOP 内容。",
        message=message,
    )


def _sop_snippet(response: ToolResponse) -> str:
    data = response.data if isinstance(response.data, dict) else {}
    results = data.get("results", [])
    if not results:
        return ""
    return str(results[0].get("chunk_text", ""))[:180]


def analyze_order_delivery_risk(
    db: Session,
    username: str,
    role: str,
    order_no: str,
    agent_call_id: int | None = None,
) -> AnalysisResponse:
    analysis_name = "analyze_order_delivery_risk"
    checked_data = ["销售订单", "销售订单明细", "SKU 库存", "采购到货", "交期异常 SOP"]
    if not is_tool_allowed(role, analysis_name):
        return _denied_response(
            db, username, role, analysis_name, {"order_no": order_no}, checked_data, agent_call_id
        )

    called_tools: list[ToolResponse] = []
    called_tools.append(
        _call(db, username, role, agent_call_id, "query_order_status", order_no=order_no)
    )
    order = _tool_data(called_tools, "query_order_status")
    shortages: list[str] = []
    purchase_signal = ""
    for item in order.get("items", []):
        inventory_response = _call(
            db,
            username,
            role,
            agent_call_id,
            "query_inventory_by_sku",
            sku_code=item["sku_code"],
        )
        called_tools.append(inventory_response)
        inventory = inventory_response.data if isinstance(inventory_response.data, dict) else {}
        shortage = item["quantity"] - inventory.get("available_quantity", 0)
        if shortage > 0:
            shortages.append(f"{item['sku_code']} 缺口 {shortage:g}")

    purchase_response = _call(
        db,
        username,
        role,
        agent_call_id,
        "query_purchase_arrival",
        purchase_order_no="PO1001",
    )
    called_tools.append(purchase_response)
    purchase = purchase_response.data if isinstance(purchase_response.data, dict) else {}
    if purchase.get("found"):
        purchase_signal = (
            f"采购单 PO1001 状态 {purchase.get('status')}，预计到货 {purchase.get('expected_arrival_date')}。"
        )

    sop_response = _call(
        db,
        username,
        role,
        agent_call_id,
        "query_exception_sop",
        question="订单库存不足 交期异常 应该怎么处理",
    )
    called_tools.append(sop_response)
    sop_text = _sop_snippet(sop_response)

    if not _all_allowed(called_tools):
        conclusion = "当前角色无权完成订单发货风险分析所需的全部工具调用。"
        action = "请使用销售、仓库、采购、生产主管或管理员角色重新分析。"
        risk_level = "blocked"
        risk_factors = ["permission_denied"]
        manual_review_reason = ["permission_denied"]
    elif not order.get("found"):
        conclusion = f"未找到订单 {order_no}，无法判断发货风险。"
        action = "请人工核对订单号后重新查询。"
        risk_level = "unknown"
        risk_factors = ["business_identifier_not_found"]
        manual_review_reason = ["business_identifier_not_found"]
    else:
        shipment_risk = analyze_shipment_risk(db, order_no)
        evidence = shipment_risk.get("evidence", [])
        recommendations = shipment_risk.get("recommendations", [])
        can_ship = shipment_risk.get("can_ship")
        partial_ship = shipment_risk.get("partial_ship")
        shortage_risk = shipment_risk.get("shortage_risk")
        delivery_delay_risk = shipment_risk.get("delivery_delay_risk")
        risk_level = str(shipment_risk.get("risk_level", "unknown"))
        risk_factors = list(shipment_risk.get("risk_factors", []))
        manual_review_reason = list(shipment_risk.get("manual_review_reason", []))
        if can_ship:
            conclusion = (
                f"\u8ba2\u5355 {order_no} \u5f53\u524d\u5e93\u5b58\u98ce\u9669\u8f83\u4f4e\uff0ccan_ship={can_ship}, partial_ship={partial_ship}, "
                f"shortage_risk={shortage_risk}, delivery_delay_risk={delivery_delay_risk}. {purchase_signal}"
            )
        else:
            conclusion = (
                f"\u8ba2\u5355 {order_no} \u6682\u4e0d\u5efa\u8bae\u81ea\u52a8\u53d1\u8d27\uff0c\u5e93\u5b58\u4e0d\u8db3\u6216\u9700\u590d\u6838\uff0ccan_ship={can_ship}, "
                f"partial_ship={partial_ship}, shortage_risk={shortage_risk}, "
                f"delivery_delay_risk={delivery_delay_risk}. {purchase_signal}"
            )
        action = " ".join(str(item) for item in recommendations)
        if sop_text:
            action = f"{action} SOP \u5efa\u8bae\u53c2\u8003\uff1a{sop_text}"

    return AnalysisResponse(
        success=_all_success(called_tools),
        permission_allowed=_all_allowed(called_tools),
        analysis_name=analysis_name,
        checked_data=checked_data,
        called_tools=called_tools,
        risk_level=risk_level,
        evidence=evidence if "evidence" in locals() else [],
        recommendations=recommendations if "recommendations" in locals() else [],
        **_review_fields(
            risk_level,
            risk_factors if "risk_factors" in locals() else [],
            manual_review_reason if "manual_review_reason" in locals() else [],
        ),
        business_conclusion=conclusion,
        suggested_next_action=action,
        message="订单发货风险分析完成。" if _all_success(called_tools) else "订单发货风险分析未完整完成。",
    )


def analyze_work_order_readiness(
    db: Session,
    username: str,
    role: str,
    work_order_no: str,
    agent_call_id: int | None = None,
) -> AnalysisResponse:
    analysis_name = "analyze_work_order_readiness"
    checked_data = ["工单", "工单用料", "物料库存", "工单缺料处理 SOP"]
    if not is_tool_allowed(role, analysis_name):
        return _denied_response(
            db,
            username,
            role,
            analysis_name,
            {"work_order_no": work_order_no},
            checked_data,
            agent_call_id,
        )

    called_tools: list[ToolResponse] = []
    called_tools.append(
        _call(db, username, role, agent_call_id, "query_work_order", work_order_no=work_order_no)
    )
    work_order = _tool_data(called_tools, "query_work_order")
    shortages: list[str] = []
    for material in work_order.get("materials", []):
        inventory_response = _call(
            db,
            username,
            role,
            agent_call_id,
            "query_inventory_by_sku",
            sku_code=material["material_sku"],
        )
        called_tools.append(inventory_response)
        inventory = inventory_response.data if isinstance(inventory_response.data, dict) else {}
        required_remaining = material["required_quantity"] - material.get("issued_quantity", 0)
        shortage = required_remaining - inventory.get("available_quantity", 0)
        if shortage > 0:
            shortages.append(f"{material['material_sku']} 缺口 {shortage:g}")

    sop_response = _call(
        db,
        username,
        role,
        agent_call_id,
        "query_exception_sop",
        question="工单 缺料 齐套 开工 应该怎么处理",
    )
    called_tools.append(sop_response)
    sop_text = _sop_snippet(sop_response)

    if not _all_allowed(called_tools):
        conclusion = "当前角色无权完成工单齐套分析所需的全部工具调用。"
        action = "请使用生产主管或管理员角色重新分析。"
        risk_level = "blocked"
        risk_factors = ["permission_denied"]
        manual_review_reason = ["permission_denied"]
    elif not work_order.get("found"):
        conclusion = f"未找到工单 {work_order_no}，无法判断开工条件。"
        action = "请人工核对工单号后重新查询。"
        risk_level = "unknown"
        risk_factors = ["business_identifier_not_found"]
        manual_review_reason = ["business_identifier_not_found"]
    elif shortages:
        conclusion = f"工单 {work_order_no} 暂不建议开工，存在缺料：{'; '.join(shortages)}。"
        action = "建议生产主管确认齐套缺口，采购跟进到货，必要时调整排产。"
        if sop_text:
            action = f"{action} SOP 建议参考：{sop_text}"
        risk_level = "high"
        risk_factors = ["work_order_material_shortage"]
        manual_review_reason = ["work_order_material_shortage"]
    else:
        conclusion = f"工单 {work_order_no} 当前主要用料可覆盖需求，可进入开工前人工复核。"
        action = "建议生产主管复核领料、设备和人员条件后，再在企业系统中确认开工动作。"
        risk_level = "low"
        risk_factors = []
        manual_review_reason = []

    return AnalysisResponse(
        success=_all_success(called_tools),
        permission_allowed=_all_allowed(called_tools),
        analysis_name=analysis_name,
        checked_data=checked_data,
        called_tools=called_tools,
        risk_level=risk_level,
        **_review_fields(risk_level, risk_factors, manual_review_reason),
        business_conclusion=conclusion,
        suggested_next_action=action,
        message="工单齐套分析完成。" if _all_success(called_tools) else "工单齐套分析未完整完成。",
    )


def analyze_purchase_delay_impact(
    db: Session,
    username: str,
    role: str,
    purchase_order_no: str,
    agent_call_id: int | None = None,
) -> AnalysisResponse:
    analysis_name = "analyze_purchase_delay_impact"
    checked_data = ["采购单", "采购明细", "相关销售订单", "采购延期沟通 SOP"]
    if not is_tool_allowed(role, analysis_name):
        return _denied_response(
            db,
            username,
            role,
            analysis_name,
            {"purchase_order_no": purchase_order_no},
            checked_data,
            agent_call_id,
        )

    called_tools: list[ToolResponse] = []
    called_tools.append(
        _call(
            db,
            username,
            role,
            agent_call_id,
            "query_purchase_arrival",
            purchase_order_no=purchase_order_no,
        )
    )
    purchase = _tool_data(called_tools, "query_purchase_arrival")
    affected_orders: list[str] = []
    if purchase.get("items"):
        sku_codes = [item["sku_code"] for item in purchase["items"]]
        rows = db.scalars(
            select(SalesOrderItem).where(SalesOrderItem.sku_code.in_(sku_codes))
        ).all()
        affected_orders = sorted({row.order_no for row in rows})
        for order_no in affected_orders:
            called_tools.append(
                _call(db, username, role, agent_call_id, "query_order_status", order_no=order_no)
            )

    sop_response = _call(
        db,
        username,
        role,
        agent_call_id,
        "query_exception_sop",
        question="采购延期 交期沟通 客户订单 应该怎么处理",
    )
    called_tools.append(sop_response)
    sop_text = _sop_snippet(sop_response)

    if not _all_allowed(called_tools):
        conclusion = "当前角色无权完成采购延期影响分析所需的全部工具调用。"
        action = "请使用采购、销售、生产主管或管理员角色重新分析。"
        risk_level = "blocked"
        risk_factors = ["permission_denied"]
        manual_review_reason = ["permission_denied"]
    elif not purchase.get("found"):
        conclusion = f"未找到采购单 {purchase_order_no}，无法判断延期影响。"
        action = "请人工核对采购单号后重新查询。"
        risk_level = "unknown"
        risk_factors = ["business_identifier_not_found"]
        manual_review_reason = ["business_identifier_not_found"]
    elif purchase.get("is_delayed"):
        orders_text = "、".join(affected_orders) if affected_orders else "暂未找到相关销售订单"
        conclusion = (
            f"采购单 {purchase_order_no} 已延期，预计到货 {purchase.get('expected_arrival_date')}，"
            f"可能影响客户订单：{orders_text}。"
        )
        action = "建议采购确认新的到货承诺，销售评估客户交期沟通，生产主管同步排产影响。"
        if sop_text:
            action = f"{action} SOP 建议参考：{sop_text}"
        risk_level = "high" if affected_orders else "medium"
        risk_factors = ["purchase_delay"]
        manual_review_reason = ["purchase_delay"] if affected_orders else []
    else:
        conclusion = f"采购单 {purchase_order_no} 当前未标记延期，暂未发现明确交付影响。"
        action = "建议采购持续跟踪预计到货日期，出现变化时同步销售和生产主管复核。"
        risk_level = "low"
        risk_factors = []
        manual_review_reason = []

    return AnalysisResponse(
        success=_all_success(called_tools),
        permission_allowed=_all_allowed(called_tools),
        analysis_name=analysis_name,
        checked_data=checked_data,
        called_tools=called_tools,
        risk_level=risk_level,
        **_review_fields(risk_level, risk_factors, manual_review_reason),
        business_conclusion=conclusion,
        suggested_next_action=action,
        message="采购延期影响分析完成。" if _all_success(called_tools) else "采购延期影响分析未完整完成。",
    )
