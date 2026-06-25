from datetime import datetime
import logging
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.core.logging import log_extra
from app.core.permissions import is_tool_allowed
from app.schemas import ToolResponse
from app.services.audit_service import create_tool_call_log
from app.tools import (
    query_exception_sop,
    query_inventory_by_sku,
    query_order_status,
    query_purchase_arrival,
    query_work_order,
)


ToolFunc = Callable[..., dict[str, Any]]

TOOL_REGISTRY: dict[str, ToolFunc] = {
    "query_order_status": query_order_status,
    "query_inventory_by_sku": query_inventory_by_sku,
    "query_work_order": query_work_order,
    "query_purchase_arrival": query_purchase_arrival,
    "query_exception_sop": query_exception_sop,
}


def execute_tool(
    db: Session,
    username: str,
    role: str,
    tool_name: str,
    tool_args: dict[str, Any],
    agent_call_id: int | None = None,
) -> ToolResponse:
    started_at = datetime.utcnow()
    logger = logging.getLogger("app.tool")
    allowed = is_tool_allowed(role, tool_name)
    if not allowed:
        message = f"角色 {role} 无权调用工具 {tool_name}。"
        create_tool_call_log(
            db=db,
            username=username,
            role=role,
            tool_name=tool_name,
            tool_args=tool_args,
            permission_allowed=False,
            success=False,
            error_message=message,
            agent_call_id=agent_call_id,
        )
        logger.info(
            "tool_permission_denied",
            extra=log_extra(
                role=role,
                tool_name=tool_name,
                success=False,
                latency_ms=0,
            ),
        )
        return ToolResponse(
            success=False,
            permission_allowed=False,
            tool_name=tool_name,
            data=None,
            message=message,
        )

    tool = TOOL_REGISTRY[tool_name]
    try:
        data = tool(db=db, **tool_args)
        latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        message = f"工具 {tool_name} 调用成功。"
        create_tool_call_log(
            db=db,
            username=username,
            role=role,
            tool_name=tool_name,
            tool_args=tool_args,
            permission_allowed=True,
            success=True,
            result_summary=str(data)[:1000],
            latency_ms=latency_ms,
            agent_call_id=agent_call_id,
        )
        logger.info(
            "tool_completed",
            extra=log_extra(
                role=role,
                tool_name=tool_name,
                success=True,
                latency_ms=latency_ms,
            ),
        )
        return ToolResponse(
            success=True,
            permission_allowed=True,
            tool_name=tool_name,
            data=data,
            message=message,
        )
    except Exception as exc:
        latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        message = f"工具 {tool_name} 调用失败：{exc}"
        create_tool_call_log(
            db=db,
            username=username,
            role=role,
            tool_name=tool_name,
            tool_args=tool_args,
            permission_allowed=True,
            success=False,
            error_message=message,
            latency_ms=latency_ms,
            agent_call_id=agent_call_id,
        )
        logger.exception(
            "tool_failed",
            extra=log_extra(
                role=role,
                tool_name=tool_name,
                success=False,
                latency_ms=latency_ms,
            ),
        )
        return ToolResponse(
            success=False,
            permission_allowed=True,
            tool_name=tool_name,
            data=None,
            message=message,
        )
