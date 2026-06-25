from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.core.request_context import get_request_id
from app.models.audit import AgentCallLog, ToolCallLog


def create_agent_call_log(
    db: Session,
    username: str,
    role: str,
    question: str,
    model_name: str = "rule-router",
) -> AgentCallLog:
    log = AgentCallLog(
        request_id=get_request_id(),
        username=username,
        role=role,
        question=question,
        success=True,
        model_name=model_name,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def finish_agent_call_log(
    db: Session,
    log: AgentCallLog,
    answer_summary: str,
    success: bool = True,
    error_message: str | None = None,
    started_at: datetime | None = None,
    intent: str | None = None,
    risk_level: str | None = None,
    response_json: dict[str, Any] | None = None,
    model_name: str | None = None,
    estimated_prompt_tokens: int | None = None,
    estimated_completion_tokens: int | None = None,
) -> AgentCallLog:
    log.answer_summary = answer_summary[:1000]
    log.intent = intent
    log.risk_level = risk_level
    log.response_json = response_json
    log.success = success
    log.error_message = error_message
    if started_at:
        log.latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
    if model_name:
        log.model_name = model_name
    log.estimated_prompt_tokens = estimated_prompt_tokens or len(log.question)
    log.estimated_completion_tokens = estimated_completion_tokens or len(answer_summary)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


def create_tool_call_log(
    db: Session,
    username: str,
    role: str,
    tool_name: str,
    tool_args: dict[str, Any],
    permission_allowed: bool,
    success: bool,
    result_summary: str | None = None,
    error_message: str | None = None,
    latency_ms: int = 0,
    agent_call_id: int | None = None,
) -> ToolCallLog:
    log = ToolCallLog(
        request_id=get_request_id(),
        agent_call_id=agent_call_id,
        username=username,
        role=role,
        tool_name=tool_name,
        tool_args_json=tool_args,
        tool_result_summary=result_summary,
        permission_allowed=permission_allowed,
        success=success,
        error_message=error_message,
        latency_ms=latency_ms,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
