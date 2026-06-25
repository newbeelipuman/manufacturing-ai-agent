from app.core.permissions import Role, is_tool_allowed
from app.db.session import SessionLocal
from app.models.inventory import InventorySku
from app.services.tool_service import TOOL_REGISTRY


def test_permission_matrix_keeps_normal_user_to_sop_only() -> None:
    business_tools = [
        "query_order_status",
        "query_inventory_by_sku",
        "query_work_order",
        "query_purchase_arrival",
        "analyze_order_delivery_risk",
        "analyze_work_order_readiness",
        "analyze_purchase_delay_impact",
    ]
    for tool_name in business_tools:
        assert not is_tool_allowed(Role.NORMAL_USER, tool_name)
    assert is_tool_allowed(Role.NORMAL_USER, "query_exception_sop")
    assert all(is_tool_allowed(Role.ADMIN, tool_name) for tool_name in TOOL_REGISTRY)
    assert is_tool_allowed(Role.SALES, "analyze_order_delivery_risk")
    assert is_tool_allowed(Role.PRODUCTION_MANAGER, "analyze_work_order_readiness")
    assert is_tool_allowed(Role.PURCHASE, "analyze_purchase_delay_impact")


def test_health(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_tool_debug_apis(client) -> None:
    cases = [
        (
            "/api/tools/query-order-status",
            {"username": "demo_sales", "role": "sales", "order_no": "O1001"},
            "query_order_status",
        ),
        (
            "/api/tools/query-inventory-by-sku",
            {"username": "demo_warehouse", "role": "warehouse", "sku_code": "SKU-KB-001"},
            "query_inventory_by_sku",
        ),
        (
            "/api/tools/query-work-order",
            {"username": "demo_pm", "role": "production_manager", "work_order_no": "WO1001"},
            "query_work_order",
        ),
        (
            "/api/tools/query-purchase-arrival",
            {"username": "demo_purchase", "role": "purchase", "purchase_order_no": "PO1001"},
            "query_purchase_arrival",
        ),
        (
            "/api/tools/query-exception-sop",
            {"username": "demo_user", "role": "normal_user", "question": "注塑件外观不良应该怎么处理？"},
            "query_exception_sop",
        ),
    ]
    for path, payload, tool_name in cases:
        response = client.post(path, json=payload)
        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["permission_allowed"] is True
        assert body["tool_name"] == tool_name


def test_composite_analysis_debug_apis_success(client) -> None:
    cases = [
        (
            "/api/tools/analyze-order-delivery-risk",
            {"username": "demo_admin", "role": "admin", "order_no": "O1001"},
            "analyze_order_delivery_risk",
            "query_order_status",
        ),
        (
            "/api/tools/analyze-work-order-readiness",
            {"username": "demo_pm", "role": "production_manager", "work_order_no": "WO1001"},
            "analyze_work_order_readiness",
            "query_work_order",
        ),
        (
            "/api/tools/analyze-purchase-delay-impact",
            {"username": "demo_purchase", "role": "purchase", "purchase_order_no": "PO1001"},
            "analyze_purchase_delay_impact",
            "query_purchase_arrival",
        ),
    ]
    for path, payload, analysis_name, expected_tool in cases:
        response = client.post(path, json=payload)
        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert body["permission_allowed"] is True
        assert body["analysis_name"] == analysis_name
        assert body["manual_confirmation_required"] is True
        assert expected_tool in [tool["tool_name"] for tool in body["called_tools"]]
        assert body["business_conclusion"]
        assert body["suggested_next_action"]


def test_composite_analysis_debug_apis_denied_are_audited(client) -> None:
    cases = [
        (
            "/api/tools/analyze-order-delivery-risk",
            {"username": "demo_user", "role": "normal_user", "order_no": "O1001"},
            "analyze_order_delivery_risk",
        ),
        (
            "/api/tools/analyze-work-order-readiness",
            {"username": "demo_user", "role": "normal_user", "work_order_no": "WO1001"},
            "analyze_work_order_readiness",
        ),
        (
            "/api/tools/analyze-purchase-delay-impact",
            {"username": "demo_user", "role": "normal_user", "purchase_order_no": "PO1001"},
            "analyze_purchase_delay_impact",
        ),
    ]
    for path, payload, analysis_name in cases:
        response = client.post(path, json=payload)
        body = response.json()
        assert response.status_code == 200
        assert body["success"] is False
        assert body["permission_allowed"] is False
        assert body["analysis_name"] == analysis_name

    logs = client.get("/api/admin/tool-call-logs?role=admin&limit=100")
    rows = logs.json()["data"]
    for _, _, analysis_name in cases:
        assert any(
            row["tool_name"] == analysis_name
            and row["permission_allowed"] is False
            and row["success"] is False
            for row in rows
        )


def test_chat_demo_questions(client) -> None:
    questions = [
        ("订单 O1001 现在能不能发货？", "query_order_status"),
        ("工单 WO1001 今天能不能开工，缺哪些物料？", "query_work_order"),
        ("采购单 PO1001 延期会影响哪些客户订单？", "query_purchase_arrival"),
        ("SKU-KB-001 当前可用库存是多少？有哪些批次？", "query_inventory_by_sku"),
        ("注塑件外观不良应该怎么处理？", "query_exception_sop"),
    ]
    for question, expected_tool in questions:
        response = client.post(
            "/api/chat",
            json={"username": "demo_admin", "role": "admin", "question": question},
        )
        body = response.json()
        assert response.status_code == 200
        assert body["success"] is True
        assert expected_tool in [tool["tool_name"] for tool in body["called_tools"]]
        assert "路由意图" in body["answer"]
        assert "分析路径" in body["answer"]
        assert "业务结论" in body["answer"]
        assert "人工确认" in body["answer"]


def test_chat_composite_routes_call_expected_tools(client) -> None:
    cases = [
        (
            "订单 O1001 因为库存不足不能发货，应该怎么处理？",
            {"query_order_status", "query_inventory_by_sku", "query_purchase_arrival", "query_exception_sop"},
            "订单发货风险分析",
        ),
        (
            "工单 WO1001 今天能不能开工，缺哪些物料？",
            {"query_work_order", "query_inventory_by_sku", "query_exception_sop"},
            "工单开工齐套分析",
        ),
        (
            "采购单 PO1001 延期会影响哪些客户订单？",
            {"query_purchase_arrival", "query_order_status", "query_exception_sop"},
            "采购延期影响分析",
        ),
    ]
    for question, expected_tools, route_intent in cases:
        response = client.post(
            "/api/chat",
            json={"username": "demo_admin", "role": "admin", "question": question},
        )
        body = response.json()
        called_tools = {tool["tool_name"] for tool in body["called_tools"]}
        assert response.status_code == 200
        assert body["success"] is True
        assert expected_tools.issubset(called_tools)
        assert route_intent in body["answer"]
        assert "建议下一步" in body["answer"]
        assert "人工确认" in body["answer"]


def test_mixed_rag_question_hits_new_sop(client) -> None:
    response = client.post(
        "/api/chat",
        json={
            "username": "demo_admin",
            "role": "admin",
            "question": "订单 O1001 因为库存不足不能发货，应该怎么处理？",
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert "库存不足" in body["business_conclusion"]
    assert "SOP" in body["suggested_next_action"]
    assert "业务结论" in body["answer"]
    assert "建议下一步" in body["answer"]
    assert "人工确认" in body["answer"]


def test_normal_user_cannot_call_composite_but_can_query_sop(client) -> None:
    denied = client.post(
        "/api/tools/analyze-order-delivery-risk",
        json={"username": "demo_user", "role": "normal_user", "order_no": "O1001"},
    )
    assert denied.status_code == 200
    assert denied.json()["permission_allowed"] is False

    allowed = client.post(
        "/api/tools/query-exception-sop",
        json={"username": "demo_user", "role": "normal_user", "question": "采购延期应该怎么沟通？"},
    )
    assert allowed.status_code == 200
    assert allowed.json()["success"] is True
    assert allowed.json()["permission_allowed"] is True


def test_normal_user_denial_is_audited(client) -> None:
    denied = client.post(
        "/api/tools/query-order-status",
        json={"username": "demo_user", "role": "normal_user", "order_no": "O1001"},
    )
    assert denied.status_code == 200
    denied_body = denied.json()
    assert denied_body["success"] is False
    assert denied_body["permission_allowed"] is False

    logs = client.get("/api/admin/tool-call-logs?role=admin")
    assert logs.status_code == 200
    rows = logs.json()["data"]
    assert any(
        row["tool_name"] == "query_order_status"
        and row["permission_allowed"] is False
        and row["success"] is False
        for row in rows
    )


def test_admin_log_apis_and_non_admin_403(client) -> None:
    client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "订单 O1001 现在能不能发货？"},
    )
    for path in [
        "/api/admin/agent-call-logs?role=admin",
        "/api/admin/tool-call-logs?role=admin",
        "/api/admin/usage-stats?role=admin",
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert response.json()["success"] is True

    denied = client.get("/api/admin/tool-call-logs?role=normal_user")
    assert denied.status_code == 403
    assert denied.json()["success"] is False


def test_sop_search_hits_injection_appearance(client) -> None:
    response = client.get("/api/knowledge/search", params={"query": "注塑件外观不良", "role": "normal_user"})
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["results"]
    assert "注塑件" in body["results"][0]["chunk_text"]
def test_knowledge_rebuild_requires_admin(client) -> None:
    allowed = client.post("/api/knowledge/rebuild?role=admin")
    assert allowed.status_code == 200
    assert allowed.json()["success"] is True

    denied = client.post("/api/knowledge/rebuild?role=normal_user")
    assert denied.status_code == 403
    assert denied.json()["success"] is False


def test_chat_response_includes_structured_orchestration_fields(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert "intent" in body
    assert "entities" in body
    assert "execution_trace" in body
    assert "risk_level" in body


def test_chat_order_question_without_order_no_asks_for_clarification(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "这个订单能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is False
    assert body["intent"] == "clarify_order_delivery_risk"
    assert body["called_tools"] == []
    assert "O1001" in body["suggested_next_action"]


def test_chat_sop_no_hit_does_not_use_search_fallback(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "完全无关的内部暗号 ABC-NO-SOP"},
    )
    body = response.json()
    assert response.status_code == 200
    assert "query_exception_sop" in [tool["tool_name"] for tool in body["called_tools"]]
    sop_tool = next(tool for tool in body["called_tools"] if tool["tool_name"] == "query_exception_sop")
    assert sop_tool["data"]["found"] is False


def test_chat_extracts_arbitrary_identifiers_and_returns_not_found(client) -> None:
    cases = [
        ("订单 O9999 现在能不能发货？", "order_no", "O9999", "unknown"),
        ("SKU-XXX 当前可用库存是多少？", "sku_code", "SKU-XXX", "unknown"),
        ("工单 WO9999 今天能不能开工？", "work_order_no", "WO9999", "unknown"),
        ("采购单 PO9999 延期会影响哪些订单？", "purchase_order_no", "PO9999", "unknown"),
    ]
    for question, key, value, risk_level in cases:
        response = client.post(
            "/api/chat",
            json={"username": "demo_admin", "role": "admin", "question": question},
        )
        body = response.json()
        assert response.status_code == 200
        assert body["entities"][key] == value
        assert body["risk_level"] == risk_level
        assert "found" in str(body["called_tools"]).lower()


def test_normal_user_order_query_returns_permission_denied_trace(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_user", "role": "normal_user", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is False
    assert body["risk_level"] == "blocked"
    assert any(
        row.get("step") == "permission"
        and row.get("tool_name") == "analyze_order_delivery_risk"
        and row.get("permission_allowed") is False
        for row in body["execution_trace"]
    )


def test_order_delivery_risk_returns_structured_shipment_risk(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["risk_level"] in {"medium", "high"}
    assert body["evidence"]
    assert body["recommendations"]
    assert "can_ship=False" in body["business_conclusion"]
    assert "库存不足" in body["business_conclusion"]


def test_order_delivery_risk_inventory_enough_scenario(client) -> None:
    db = SessionLocal()
    try:
        sku = db.query(InventorySku).filter(InventorySku.sku_code == "SKU-KB-001").one()
        sku.available_quantity = 200
        sku.quality_hold_quantity = 0
        db.commit()
    finally:
        db.close()

    response = client.post(
        "/api/chat",
        json={"username": "demo_admin", "role": "admin", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["risk_level"] == "low"
    assert "can_ship=True" in body["business_conclusion"]


def test_order_delivery_risk_denied_does_not_calculate_shipment_risk(client) -> None:
    response = client.post(
        "/api/chat",
        json={"username": "demo_user", "role": "normal_user", "question": "订单 O1001 现在能不能发货？"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["risk_level"] == "blocked"
    assert body["evidence"] == []
    assert body["recommendations"] == []

    logs = client.get("/api/admin/tool-call-logs?role=admin&limit=100")
    rows = logs.json()["data"]
    assert any(
        row["tool_name"] == "analyze_order_delivery_risk"
        and row["permission_allowed"] is False
        for row in rows
    )
