from typing import Any

from app.schemas import ToolResponse
from app.services.tool_planner import ToolPlan


def trace_step(step: str, status: str, detail: str, **extra: Any) -> dict[str, Any]:
    row: dict[str, Any] = {"step": step, "status": status, "detail": detail}
    row.update(extra)
    return row


def build_initial_trace(
    intent: str,
    entities: dict[str, Any],
    plan: ToolPlan,
    permission_rows: list[dict[str, object]],
) -> list[dict[str, Any]]:
    trace = [
        trace_step("intent", "matched", intent),
        trace_step("entities", "extracted", str(entities)),
    ]
    trace.extend(trace_step("plan", "planned", step) for step in plan.analysis_path)
    trace.extend(dict(row) for row in permission_rows)
    return trace


def tool_trace(called_tools: list[ToolResponse]) -> list[dict[str, Any]]:
    return [
        trace_step(
            "tool",
            "success" if tool.success else "failed",
            tool.message,
            tool_name=tool.tool_name,
            permission_allowed=tool.permission_allowed,
        )
        for tool in called_tools
    ]
