from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]


def test_p5_high_risk_order_requires_human_review(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_sales", "role": "sales", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["requires_human_review"] is True
    assert "inventory_shortage" in body["manual_review_reason"]
    assert body["decision_record"]["risk_result"]["requires_human_review"] is True


def test_p5_normal_user_denied_has_manual_review_reason(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_user", "role": "normal_user", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is False
    assert body["requires_human_review"] is True
    assert "permission_denied" in body["manual_review_reason"]


def test_clarification_response_is_business_readable_chinese(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "现在有哪些工单需要人工审核"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is False
    assert "工单号" in body["business_conclusion"]
    assert "WO1001" in body["suggested_next_action"]
    assert "Missing required" not in body["answer"]
    assert "Please provide" not in body["answer"]


def test_p5_admin_detail_and_usage_stats_enhanced(client) -> None:
    client.post(
        "/api/chat",
        json={"username": "demo_sales", "role": "sales", "question": "订单 O1001 现在能不能发货？"},
    )
    logs = client.get("/api/admin/agent-call-logs?role=admin&limit=1").json()["data"]
    detail = client.get(f"/api/admin/agent-call-logs/{logs[0]['id']}?role=admin")
    detail_body = detail.json()
    assert detail.status_code == 200
    assert "decision_record" in detail_body
    assert detail_body["decision_record"]["plan"]
    assert "response_json" in detail_body
    assert "tool_calls" in detail_body
    assert "execution_trace" in detail_body

    today = date.today().isoformat()
    old_day = (date.today() - timedelta(days=30)).isoformat()
    current = client.get(f"/api/admin/usage-stats?role=admin&date_from={today}&date_to={today}")
    empty = client.get(f"/api/admin/usage-stats?role=admin&date_from={old_day}&date_to={old_day}")
    body = current.json()
    assert current.status_code == 200
    assert body["total_agent_calls"] >= 1
    assert empty.json()["total_agent_calls"] == 0
    for key in ["success_rate", "denied_rate", "avg_latency_ms", "top_tools", "top_intents"]:
        assert key in body


def test_p6_sop_returns_scored_source_and_normal_user_boundaries(client) -> None:
    sop = client.post(
        "/api/tools/query-exception-sop",
        json={"username": "demo_user", "role": "normal_user", "question": "注塑件外观不良应该怎么处理？"},
    )
    result = sop.json()["data"]["results"][0]
    assert sop.status_code == 200
    assert sop.json()["permission_allowed"] is True
    assert result["source_path"]
    assert result["score"] > 0
    assert result["matched_terms"]

    for path, payload in [
        ("/api/tools/query-order-status", {"order_no": "O1001"}),
        ("/api/tools/query-inventory-by-sku", {"sku_code": "SKU-KB-001"}),
        ("/api/tools/query-work-order", {"work_order_no": "WO1001"}),
        ("/api/tools/query-purchase-arrival", {"purchase_order_no": "PO1001"}),
    ]:
        response = client.post(
            path,
            json={"username": "demo_user", "role": "normal_user", **payload},
        )
        assert response.status_code == 200
        assert response.json()["permission_allowed"] is False


def test_p6_rag_eval_script_generates_report(client) -> None:
    result = subprocess.run(
        [sys.executable, "scripts/run_rag_eval.py"],
        cwd=ROOT_DIR,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    report = ROOT_DIR / "docs" / "rag-eval-report.md"
    assert report.exists()
    assert "matched_terms" in report.read_text(encoding="utf-8")


def test_mock_llm_gateway_route_and_audit_tokens(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "SKU-KB-001 当前可用库存是多少？有哪些批次？"},
    )
    body = response.json()
    route = body["decision_record"]["llm_route"]
    assert route["provider"] == "mock"
    assert route["model"] == "mock-enterprise-agent"
    assert route["prompt_tokens"] > 0
    assert route["completion_tokens"] > 0

    log = client.get("/api/admin/agent-call-logs?role=admin&limit=1").json()["data"][0]
    assert log["model_name"] == "mock-enterprise-agent"
    assert log["estimated_prompt_tokens"] > 0
    assert log["estimated_completion_tokens"] > 0


def test_p7_business_depth_and_read_only_review_recommendations(client) -> None:
    order = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "订单 O1001 现在能不能发货？"},
    ).json()
    assert {"inventory_shortage", "quality_hold", "purchase_delay"}.intersection(
        set(order["risk_factors"])
    )
    assert order["requires_human_review"] is True
    assert "人工" in order["suggested_next_action"] or "review" in order["suggested_next_action"].lower()

    work_order = client.post(
        "/api/chat",
        json={"username": "demo_pm", "role": "production_manager", "question": "工单 WO1001 今天能不能开工，缺哪些物料？"},
    ).json()
    assert "work_order_material_shortage" in work_order["manual_review_reason"]

    purchase = client.post(
        "/api/chat",
        json={"username": "demo_purchase", "role": "purchase", "question": "采购单 PO1001 延期会影响哪些客户订单？"},
    ).json()
    assert "O1001" in purchase["business_conclusion"]
    assert "purchase_delay" in purchase["manual_review_reason"]
