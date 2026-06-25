from app.core.permissions import is_tool_allowed
from app.services.tool_planner import ToolPlan


def precheck_plan(role: str, plan: ToolPlan) -> list[dict[str, object]]:
    """Return permission trace rows without replacing execute_tool checks."""
    return [
        {
            "step": "permission",
            "status": "allowed" if is_tool_allowed(role, tool_name) else "denied",
            "tool_name": tool_name,
            "permission_allowed": is_tool_allowed(role, tool_name),
        }
        for tool_name in plan.tools
    ]
