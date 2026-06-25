from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.schemas import ChatResponse, ToolResponse
from app.services.analysis_service import (
    analyze_order_delivery_risk,
    analyze_purchase_delay_impact,
    analyze_work_order_readiness,
)
from app.services.answer_composer import compose_answer, compose_clarification
from app.services.audit_service import create_agent_call_log, finish_agent_call_log
from app.services.entity_extractor import extract_entities
from app.services.execution_trace import build_initial_trace, tool_trace, trace_step
from app.services.intent_service import detect_intent
from app.services.llm_gateway_service import route_llm_request
from app.services.permission_guard import precheck_plan
from app.services.response_filter import filter_chat_response
from app.services.tool_planner import build_tool_plan, missing_entities
from app.services.tool_service import execute_tool
from app.services.usage_service import record_usage


def _tool_data(called_tools: list[ToolResponse], tool_name: str) -> dict[str, Any]:
    for tool in called_tools:
        if tool.tool_name == tool_name and isinstance(tool.data, dict):
            return tool.data
    return {}


def _call(
    db: Session,
    username: str,
    role: str,
    agent_call_id: int,
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


def _tool_result_summary(called_tools: list[ToolResponse]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tool in called_tools:
        data = tool.data if isinstance(tool.data, dict) else {}
        rows.append(
            {
                "tool_name": tool.tool_name,
                "success": tool.success,
                "permission_allowed": tool.permission_allowed,
                "found": data.get("found"),
                "message": tool.message,
            }
        )
    return rows


def _risk_result(response: ChatResponse) -> dict[str, Any]:
    return {
        "risk_level": response.risk_level,
        "risk_factors": response.risk_factors,
        "requires_human_review": response.requires_human_review,
        "manual_review_reason": response.manual_review_reason,
    }


def _decision_record(
    response: ChatResponse,
    plan: list[str],
    permission_results: list[dict[str, object]],
    llm_route: dict[str, Any],
) -> dict[str, Any]:
    return {
        "plan": plan,
        "permission_results": permission_results,
        "tool_result_summary": _tool_result_summary(response.called_tools),
        "risk_result": _risk_result(response),
        "llm_route": llm_route,
        "final_decision": {
            "success": response.success,
            "business_conclusion": response.business_conclusion,
            "suggested_next_action": response.suggested_next_action,
        },
    }


def _review_from_tools(
    called_tools: list[ToolResponse],
    risk_level: str,
    not_found_reason: str = "business_identifier_not_found",
) -> tuple[list[str], bool, list[str]]:
    reasons: list[str] = []
    factors: list[str] = []
    if any(not tool.permission_allowed for tool in called_tools):
        reasons.append("permission_denied")
        factors.append("permission_denied")
    for tool in called_tools:
        if isinstance(tool.data, dict) and tool.data.get("found") is False:
            reasons.append(not_found_reason)
            factors.append(not_found_reason)
    if risk_level in {"high", "blocked"} and not reasons:
        reasons.append("clarification_required")
    reasons = list(dict.fromkeys(reasons))
    factors = list(dict.fromkeys(factors))
    return factors, bool(reasons or risk_level in {"high", "blocked"}), reasons


def _finish(
    db: Session,
    started_at: datetime,
    agent_log: Any,
    response: ChatResponse,
    username: str,
    role: str,
    plan_steps: list[str],
    permission_results: list[dict[str, object]],
    llm_route: dict[str, Any],
) -> ChatResponse:
    response = filter_chat_response(response, role)
    decision_record = _decision_record(response, plan_steps, permission_results, llm_route)
    response = response.model_copy(update={"decision_record": decision_record})
    finish_agent_call_log(
        db,
        agent_log,
        answer_summary=response.answer,
        success=response.success,
        started_at=started_at,
        intent=response.intent,
        risk_level=response.risk_level,
        response_json=response.model_dump(mode="json"),
        model_name=llm_route.get("model"),
        estimated_prompt_tokens=llm_route.get("prompt_tokens"),
        estimated_completion_tokens=llm_route.get("completion_tokens"),
    )
    record_usage(
        db,
        username=username,
        role=role,
        tool_call_count=len(response.called_tools),
        estimated_tokens=len(response.question) + len(response.answer),
    )
    return response


def _analysis_response(
    question: str,
    intent: str,
    entities: dict[str, Any],
    analysis_path: list[str],
    analysis: Any,
    initial_trace: list[dict[str, Any]],
) -> ChatResponse:
    return ChatResponse(
        success=analysis.success,
        question=question,
        answer=compose_answer(
            intent,
            analysis_path,
            analysis.checked_data,
            analysis.called_tools,
            analysis.business_conclusion,
            analysis.suggested_next_action,
        ),
        checked_data=analysis.checked_data,
        called_tools=analysis.called_tools,
        business_conclusion=analysis.business_conclusion,
        suggested_next_action=analysis.suggested_next_action,
        intent=intent,
        entities=entities,
        execution_trace=initial_trace + tool_trace(analysis.called_tools),
        risk_level=analysis.risk_level,
        evidence=analysis.evidence,
        recommendations=analysis.recommendations,
        risk_factors=analysis.risk_factors,
        requires_human_review=analysis.requires_human_review,
        manual_review_reason=analysis.manual_review_reason,
    )


def chat(db: Session, username: str, role: str, question: str) -> ChatResponse:
    started_at = datetime.utcnow()
    agent_log = create_agent_call_log(db, username=username, role=role, question=question)

    entities = extract_entities(question)
    intent = detect_intent(question, entities)
    llm_route = route_llm_request(question=question, intent=intent, role=role)
    agent_log.model_name = llm_route["model"]
    agent_log.estimated_prompt_tokens = llm_route["prompt_tokens"]
    agent_log.estimated_completion_tokens = llm_route["completion_tokens"]
    db.add(agent_log)
    db.commit()
    plan = build_tool_plan(intent, entities)
    permission_rows = precheck_plan(role, plan)
    trace = build_initial_trace(intent, entities, plan, permission_rows)
    missing = missing_entities(plan)

    if intent.startswith("clarify_") or missing:
        missing_names = missing or plan.required_entities or ["business identifier"]
        answer, conclusion, action = compose_clarification(intent, missing_names, entities)
        response = ChatResponse(
            success=False,
            question=question,
            answer=answer,
            checked_data=[],
            called_tools=[],
            business_conclusion=conclusion,
            suggested_next_action=action,
            intent=intent,
            entities=entities,
            execution_trace=trace
            + [trace_step("tool", "skipped", "No business tool called before clarification.")],
            risk_level="unknown",
            risk_factors=["clarification_required"],
            requires_human_review=True,
            manual_review_reason=["clarification_required"],
        )
        return _finish(
            db,
            started_at,
            agent_log,
            response,
            username,
            role,
            plan.analysis_path,
            permission_rows,
            llm_route,
        )

    if intent == "order_delivery_risk":
        analysis = analyze_order_delivery_risk(
            db=db,
            username=username,
            role=role,
            order_no=entities["order_no"],
            agent_call_id=agent_log.id,
        )
        response = _analysis_response(
            question, intent, entities, plan.analysis_path, analysis, trace
        )
        return _finish(db, started_at, agent_log, response, username, role, plan.analysis_path, permission_rows, llm_route)

    if intent == "work_order_readiness":
        analysis = analyze_work_order_readiness(
            db=db,
            username=username,
            role=role,
            work_order_no=entities["work_order_no"],
            agent_call_id=agent_log.id,
        )
        response = _analysis_response(
            question, intent, entities, plan.analysis_path, analysis, trace
        )
        return _finish(db, started_at, agent_log, response, username, role, plan.analysis_path, permission_rows, llm_route)

    if intent == "purchase_delay_impact":
        analysis = analyze_purchase_delay_impact(
            db=db,
            username=username,
            role=role,
            purchase_order_no=entities["purchase_order_no"],
            agent_call_id=agent_log.id,
        )
        response = _analysis_response(
            question, intent, entities, plan.analysis_path, analysis, trace
        )
        return _finish(db, started_at, agent_log, response, username, role, plan.analysis_path, permission_rows, llm_route)

    called_tools: list[ToolResponse] = []
    if intent == "inventory_batches":
        called_tools.append(
            _call(
                db,
                username,
                role,
                agent_log.id,
                "query_inventory_by_sku",
                sku_code=entities["sku_code"],
            )
        )
        inventory = _tool_data(called_tools, "query_inventory_by_sku")
        if not called_tools[0].permission_allowed:
            conclusion = f"Role {role} is not allowed to query inventory."
            action = "Use an authorized business role or ask only public SOP questions."
            risk_level = "blocked"
        elif not inventory.get("found"):
            conclusion = f"SKU {entities['sku_code']} was not found."
            action = "Check the SKU code and retry."
            risk_level = "unknown"
        else:
            batches = ", ".join(
                f"{batch['batch_no']}@{batch['warehouse_code']} available {batch['available_quantity']:g}"
                for batch in inventory.get("batches", [])
            )
            conclusion = (
                f"SKU {entities['sku_code']} available inventory is "
                f"{inventory.get('available_quantity', 0):g} {inventory.get('unit', '')}; "
                f"batches: {batches or 'none'}."
            )
            action = "Warehouse should review batch status and locked quantity before any shipment action."
            risk_level = "low"
        risk_factors, requires_human_review, manual_review_reason = _review_from_tools(
            called_tools, risk_level
        )
        response = ChatResponse(
            success=all(tool.success for tool in called_tools),
            question=question,
            answer=compose_answer(
                intent,
                plan.analysis_path,
                ["SKU inventory", "inventory batches", "warehouse stock"],
                called_tools,
                conclusion,
                action,
            ),
            checked_data=["SKU inventory", "inventory batches", "warehouse stock"],
            called_tools=called_tools,
            business_conclusion=conclusion,
            suggested_next_action=action,
            intent=intent,
            entities=entities,
            execution_trace=trace + tool_trace(called_tools),
            risk_level=risk_level,
            risk_factors=risk_factors,
            requires_human_review=requires_human_review,
            manual_review_reason=manual_review_reason,
        )
        return _finish(db, started_at, agent_log, response, username, role, plan.analysis_path, permission_rows, llm_route)

    called_tools.append(
        _call(
            db,
            username,
            role,
            agent_log.id,
            "query_exception_sop",
            question=question,
        )
    )
    sop = _tool_data(called_tools, "query_exception_sop")
    results = sop.get("results", [])
    if not called_tools[0].permission_allowed:
        conclusion = f"当前角色 {role} 没有查询异常 SOP 的权限。"
        action = "请切换到已授权角色，或在权限中心提交菜单/知识库访问申请。"
        risk_level = "blocked"
    elif results:
        snippet = str(results[0].get("chunk_text", ""))[:180]
        conclusion = f"已匹配到异常处理 SOP，可参考片段：{snippet}"
        action = "按 SOP 步骤处理，并由质量或生产负责人确认高风险动作。"
        risk_level = "medium"
    else:
        conclusion = "未找到匹配的 SOP 片段。"
        action = "请调整关键词，或由管理员补充相关 SOP 文档后重建知识库。"
        risk_level = "unknown"
    risk_factors, requires_human_review, manual_review_reason = _review_from_tools(
        called_tools, risk_level
    )
    response = ChatResponse(
        success=all(tool.success for tool in called_tools),
        question=question,
        answer=compose_answer(
            intent,
            plan.analysis_path,
            ["SOP 知识片段"],
            called_tools,
            conclusion,
            action,
        ),
        checked_data=["SOP 知识片段"],
        called_tools=called_tools,
        business_conclusion=conclusion,
        suggested_next_action=action,
        intent=intent,
        entities=entities,
        execution_trace=trace + tool_trace(called_tools),
        risk_level=risk_level,
        risk_factors=risk_factors,
        requires_human_review=requires_human_review,
        manual_review_reason=manual_review_reason,
    )
    return _finish(db, started_at, agent_log, response, username, role, plan.analysis_path, permission_rows, llm_route)
