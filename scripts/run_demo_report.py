from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import sys
from typing import Any

from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.main import app
from scripts.seed_demo_data import seed_demo_data


REPORT_PATH = ROOT_DIR / "docs" / "demo-report.md"

CASES = [
    {
        "title": "订单发货风险，销售可查询",
        "role": "sales",
        "username": "demo_sales",
        "question": "订单 O1001 现在能不能发货？",
    },
    {
        "title": "工单开工齐套，生产主管可查询",
        "role": "production_manager",
        "username": "demo_pm",
        "question": "工单 WO1001 今天能不能开工，缺哪些物料？",
    },
    {
        "title": "采购延期影响，采购可查询",
        "role": "purchase",
        "username": "demo_purchase",
        "question": "采购单 PO1001 延期会影响哪些客户订单？",
    },
    {
        "title": "库存批次，仓库可查询",
        "role": "warehouse",
        "username": "demo_warehouse",
        "question": "SKU-KB-001 当前可用库存是多少？有哪些批次？",
    },
    {
        "title": "异常 SOP，普通用户可查询公开知识",
        "role": "normal_user",
        "username": "demo_user",
        "question": "注塑件外观不良应该怎么处理？",
    },
    {
        "title": "订单发货风险，普通用户被拒绝",
        "role": "normal_user",
        "username": "demo_user",
        "question": "订单 O1001 现在能不能发货？",
    },
    {
        "title": "管理员查看完整链路",
        "role": "admin",
        "username": "demo_admin",
        "question": "订单 O1001 现在能不能发货？",
    },
]


def _latest_agent_call_id(client: TestClient) -> int | None:
    response = client.get("/api/admin/agent-call-logs?role=admin&limit=1")
    if response.status_code != 200:
        return None
    rows = response.json().get("data", [])
    if not rows:
        return None
    return rows[0].get("id")


def _agent_call_detail(client: TestClient, call_id: int | None) -> dict[str, Any]:
    if call_id is None:
        return {}
    response = client.get(f"/api/admin/agent-call-logs/{call_id}?role=admin")
    if response.status_code != 200:
        return {}
    return response.json()


def _tool_names(body: dict[str, Any]) -> list[str]:
    return [tool.get("tool_name", "") for tool in body.get("called_tools", [])]


def _audited_tool_names(detail: dict[str, Any]) -> list[str]:
    return [tool.get("tool_name", "") for tool in detail.get("tool_calls", [])]


def _permission_summary(body: dict[str, Any], detail: dict[str, Any]) -> str:
    tools = body.get("called_tools", [])
    if tools:
        parts = [
            f"{tool.get('tool_name')}={'allowed' if tool.get('permission_allowed') else 'denied'}"
            for tool in tools
        ]
        return ", ".join(parts)
    audited_tools = detail.get("tool_calls", [])
    if not audited_tools:
        return "no tool called"
    parts = [f"{tool.get('tool_name')}={tool.get('status')}" for tool in audited_tools]
    return ", ".join(parts)


def _case_section(result: dict[str, Any]) -> str:
    body = result["body"]
    detail = result.get("detail", {})
    tools = _tool_names(body) or _audited_tool_names(detail)
    return "\n".join(
        [
            f"## {result['index']}. {result['title']}",
            "",
            f"- question: {result['question']}",
            f"- role: `{result['role']}`",
            f"- http_status: `{result['status_code']}`",
            f"- success: `{body.get('success')}`",
            f"- intent: `{body.get('intent')}`",
            f"- entities: `{json.dumps(body.get('entities', {}), ensure_ascii=False)}`",
            f"- called_tools: `{', '.join(tools) or 'none'}`",
            f"- permission: `{_permission_summary(body, detail)}`",
            f"- risk_level: `{body.get('risk_level')}`",
            f"- business_conclusion: {body.get('business_conclusion')}",
            f"- agent_call_id: `{result.get('agent_call_id')}`",
            "",
            "answer:",
            "",
            "```text",
            body.get("answer", ""),
            "```",
            "",
        ]
    )


def build_report(results: list[dict[str, Any]]) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Demo Report",
        "",
        f"Generated at: {generated_at}",
        "",
        "本报告由 `python scripts/run_demo_report.py` 生成。脚本会先重置并 seed 模拟 ERP/MES/WMS 数据，然后通过 FastAPI TestClient 调用 `/api/chat`。",
        "",
        "覆盖范围：5 个必答问题、admin/sales/warehouse/purchase/production_manager/normal_user 代表角色、允许与拒绝的权限路径、审计日志 call id。",
        "",
    ]
    for result in results:
        lines.append(_case_section(result))
    return "\n".join(lines)


def main() -> None:
    seed_demo_data()
    results: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for index, case in enumerate(CASES, start=1):
            response = client.post(
                "/api/chat",
                json={
                    "username": case["username"],
                    "role": case["role"],
                    "question": case["question"],
                },
            )
            body = response.json()
            agent_call_id = _latest_agent_call_id(client)
            results.append(
                {
                    "index": index,
                    "title": case["title"],
                    "role": case["role"],
                    "question": case["question"],
                    "status_code": response.status_code,
                    "body": body,
                    "agent_call_id": agent_call_id,
                    "detail": _agent_call_detail(client, agent_call_id),
                }
            )

    REPORT_PATH.write_text(build_report(results), encoding="utf-8")
    print(f"Demo report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
