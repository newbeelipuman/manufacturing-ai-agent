from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.permissions import is_admin
from app.db.session import get_db
from app.models.audit import AgentCallLog, ToolCallLog, UsageStat
from app.schemas import AdminListResponse
from app.services.auth_service import ensure_permission, resolve_identity

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_admin(role: str) -> None:
    if not is_admin(role):
        raise HTTPException(status_code=403, detail="仅 admin 角色可以访问管理接口。")


def _require_admin_permission(
    db: Session, identity: dict[str, str], permission_code: str
) -> None:
    _require_admin(identity["role"])
    ensure_permission(db, identity["username"], permission_code)


def _to_dict(row: object) -> dict[str, object]:
    return {
        column.name: getattr(row, column.name)
        for column in row.__table__.columns  # type: ignore[attr-defined]
    }


def _status(row: ToolCallLog) -> str:
    if not row.permission_allowed:
        return "denied"
    return "success" if row.success else "failed"


def _tool_call_dict(row: ToolCallLog) -> dict[str, Any]:
    return {
        "id": row.id,
        "tool_name": row.tool_name,
        "status": _status(row),
        "allowed": row.permission_allowed,
        "success": row.success,
        "error_message": row.error_message,
        "latency_ms": row.latency_ms,
        "created_at": row.created_at,
    }


def _tool_call_detail_dict(row: ToolCallLog) -> dict[str, Any]:
    return {
        "success": True,
        "id": row.id,
        "request_id": row.request_id,
        "agent_call_id": row.agent_call_id,
        "username": row.username,
        "role": row.role,
        "tool_name": row.tool_name,
        "status": _status(row),
        "permission_allowed": row.permission_allowed,
        "success_flag": row.success,
        "tool_args_json": row.tool_args_json or {},
        "tool_result_summary": row.tool_result_summary,
        "error_message": row.error_message,
        "latency_ms": row.latency_ms,
        "created_at": row.created_at,
    }


@router.get(
    "/agent-call-logs",
    response_model=AdminListResponse,
    summary="List agent call audit logs",
)
def get_agent_call_logs(
    request: Request,
    role: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    request_id: str | None = Query(None),
    username: str | None = Query(None),
    log_role: str | None = Query(None),
    intent: str | None = Query(None),
    risk_level: str | None = Query(None),
    success: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> AdminListResponse:
    identity = resolve_identity(request, fallback_role=role)
    _require_admin_permission(db, identity, "api:admin-agent-logs")
    query = select(AgentCallLog)
    if request_id:
        query = query.where(AgentCallLog.request_id == request_id)
    if username:
        query = query.where(AgentCallLog.username == username)
    if log_role:
        query = query.where(AgentCallLog.role == log_role)
    if intent:
        query = query.where(AgentCallLog.intent == intent)
    if risk_level:
        query = query.where(AgentCallLog.risk_level == risk_level)
    if success is not None:
        query = query.where(AgentCallLog.success == success)
    rows = db.scalars(query.order_by(AgentCallLog.id.desc()).limit(limit)).all()
    return AdminListResponse(success=True, data=[_to_dict(row) for row in rows])


@router.get(
    "/agent-call-logs/{call_id}",
    summary="Get one agent call audit log with tool calls",
)
def get_agent_call_log_detail(
    call_id: int,
    request: Request,
    role: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request, fallback_role=role)
    _require_admin_permission(db, identity, "api:admin-agent-logs")
    row = db.get(AgentCallLog, call_id)
    if row is None:
        raise HTTPException(status_code=404, detail="agent call log not found")

    tool_rows = db.scalars(
        select(ToolCallLog)
        .where(ToolCallLog.agent_call_id == call_id)
        .order_by(ToolCallLog.id.asc())
    ).all()
    response_json = row.response_json or {}
    return {
        "success": True,
        "call_id": row.id,
        "question": row.question,
        "user_role": row.role,
        "username": row.username,
        "intent": row.intent or response_json.get("intent") or "unknown",
        "entities": response_json.get("entities") or {},
        "risk_level": row.risk_level or response_json.get("risk_level") or "unknown",
        "answer_summary": row.answer_summary,
        "response_json": response_json,
        "decision_record": response_json.get("decision_record") or {},
        "execution_trace": response_json.get("execution_trace") or [],
        "tool_calls": [_tool_call_dict(tool_row) for tool_row in tool_rows],
        "created_at": row.created_at,
    }


@router.get(
    "/tool-call-logs",
    response_model=AdminListResponse,
    summary="List tool call audit logs",
)
def get_tool_call_logs(
    request: Request,
    role: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    request_id: str | None = Query(None),
    username: str | None = Query(None),
    log_role: str | None = Query(None),
    tool_name: str | None = Query(None),
    permission_allowed: bool | None = Query(None),
    success: bool | None = Query(None),
    db: Session = Depends(get_db),
) -> AdminListResponse:
    identity = resolve_identity(request, fallback_role=role)
    _require_admin_permission(db, identity, "api:admin-tool-logs")
    query = select(ToolCallLog)
    if request_id:
        query = query.where(ToolCallLog.request_id == request_id)
    if username:
        query = query.where(ToolCallLog.username == username)
    if log_role:
        query = query.where(ToolCallLog.role == log_role)
    if tool_name:
        query = query.where(ToolCallLog.tool_name == tool_name)
    if permission_allowed is not None:
        query = query.where(ToolCallLog.permission_allowed == permission_allowed)
    if success is not None:
        query = query.where(ToolCallLog.success == success)
    rows = db.scalars(query.order_by(ToolCallLog.id.desc()).limit(limit)).all()
    return AdminListResponse(success=True, data=[_to_dict(row) for row in rows])


@router.get(
    "/tool-call-logs/{log_id}",
    summary="Get one tool call audit log detail",
)
def get_tool_call_log_detail(
    log_id: int,
    request: Request,
    role: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request, fallback_role=role)
    _require_admin_permission(db, identity, "api:admin-tool-logs")
    row = db.get(ToolCallLog, log_id)
    if row is None:
        raise HTTPException(status_code=404, detail="tool call log not found")
    return _tool_call_detail_dict(row)


@router.get(
    "/usage-stats",
    summary="Get usage statistics summary",
)
def get_usage_stats(
    request: Request,
    role: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request, fallback_role=role)
    _require_admin_permission(db, identity, "api:admin-usage-stats")
    agent_query = select(AgentCallLog)
    tool_query = select(ToolCallLog)
    usage_query = select(UsageStat)
    if date_from:
        start_dt = datetime.combine(date_from, time.min)
        agent_query = agent_query.where(AgentCallLog.created_at >= start_dt)
        tool_query = tool_query.where(ToolCallLog.created_at >= start_dt)
        usage_query = usage_query.where(UsageStat.date >= date_from)
    if date_to:
        end_dt = datetime.combine(date_to + timedelta(days=1), time.min)
        agent_query = agent_query.where(AgentCallLog.created_at < end_dt)
        tool_query = tool_query.where(ToolCallLog.created_at < end_dt)
        usage_query = usage_query.where(UsageStat.date <= date_to)

    agent_rows = db.scalars(agent_query).all()
    tool_rows = db.scalars(tool_query).all()
    usage_rows = db.scalars(usage_query).all()

    tool_calls_by_name = Counter(row.tool_name for row in tool_rows)
    agent_calls_by_role = Counter(row.role for row in agent_rows)
    denied_rows = [row for row in tool_rows if not row.permission_allowed]
    permission_denied_by_role = Counter(row.role for row in denied_rows)
    risk_level_distribution = Counter(row.risk_level or "unknown" for row in agent_rows)
    intent_distribution = Counter(row.intent or "unknown" for row in agent_rows)
    successful_agent_calls = sum(1 for row in agent_rows if row.success)
    success_rate = successful_agent_calls / len(agent_rows) if agent_rows else 0
    denied_rate = len(denied_rows) / len(tool_rows) if tool_rows else 0
    avg_latency_ms = (
        sum(row.latency_ms or 0 for row in agent_rows) / len(agent_rows) if agent_rows else 0
    )

    return {
        "success": True,
        "total_agent_calls": len(agent_rows),
        "total_tool_calls": len(tool_rows),
        "total_usage_requests": sum(row.request_count for row in usage_rows),
        "total_estimated_tokens": sum(row.estimated_tokens for row in usage_rows),
        "tool_calls_by_name": dict(tool_calls_by_name),
        "agent_calls_by_role": dict(agent_calls_by_role),
        "permission_denied_count": len(denied_rows),
        "permission_denied_by_role": dict(permission_denied_by_role),
        "risk_level_distribution": dict(risk_level_distribution),
        "intent_distribution": dict(intent_distribution),
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "success_rate": round(success_rate, 4),
        "denied_rate": round(denied_rate, 4),
        "avg_latency_ms": round(avg_latency_ms, 2),
        "top_tools": tool_calls_by_name.most_common(5),
        "top_intents": intent_distribution.most_common(5),
    }


@router.get("/metrics", summary="Get operational metrics")
def get_metrics(
    request: Request,
    role: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request, fallback_role=role)
    _require_admin_permission(db, identity, "api:admin-usage-stats")

    agent_rows = db.scalars(select(AgentCallLog)).all()
    tool_rows = db.scalars(select(ToolCallLog)).all()
    denied_rows = [row for row in tool_rows if not row.permission_allowed]
    successful_agent_calls = sum(1 for row in agent_rows if row.success)
    avg_latency_ms = (
        sum(row.latency_ms or 0 for row in agent_rows) / len(agent_rows)
        if agent_rows
        else 0
    )
    high_risk_count = sum(1 for row in agent_rows if row.risk_level == "high")

    return {
        "success": True,
        "total_requests": len(agent_rows),
        "total_agent_calls": len(agent_rows),
        "total_tool_calls": len(tool_rows),
        "success_rate": round(successful_agent_calls / len(agent_rows), 4)
        if agent_rows
        else 0,
        "denied_rate": round(len(denied_rows) / len(tool_rows), 4)
        if tool_rows
        else 0,
        "avg_latency_ms": round(avg_latency_ms, 2),
        "high_risk_count": high_risk_count,
    }
