from app.services.response_filter import filter_response_by_role


def test_agent_call_detail_api_success_and_denied_tool_visible(client) -> None:
    chat = client.post(
        "/api/chat",
        json={
            "username": "demo_user",
            "role": "normal_user",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    assert chat.status_code == 200

    logs = client.get("/api/admin/agent-call-logs?role=admin&limit=1")
    call_id = logs.json()["data"][0]["id"]

    detail = client.get(f"/api/admin/agent-call-logs/{call_id}?role=admin")
    body = detail.json()
    assert detail.status_code == 200
    assert body["success"] is True
    assert body["question"]
    assert body["user_role"] == "normal_user"
    assert "tool_calls" in body
    assert any(tool["status"] == "denied" for tool in body["tool_calls"])


def test_agent_call_detail_api_rejects_non_admin_and_missing_id(client) -> None:
    denied = client.get("/api/admin/agent-call-logs/1?role=normal_user")
    assert denied.status_code == 403

    missing = client.get("/api/admin/agent-call-logs/999999?role=admin")
    assert missing.status_code == 404


def test_usage_stats_returns_platform_summary(client) -> None:
    client.post(
        "/api/chat",
        json={
            "username": "demo_sales",
            "role": "sales",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    client.post(
        "/api/chat",
        json={
            "username": "demo_user",
            "role": "normal_user",
            "question": "订单 O1001 现在能不能发货？",
        },
    )

    response = client.get("/api/admin/usage-stats?role=admin")
    body = response.json()
    assert response.status_code == 200
    assert body["success"] is True
    assert body["total_agent_calls"] >= 2
    assert body["total_tool_calls"] >= 1
    assert "tool_calls_by_name" in body
    assert "agent_calls_by_role" in body
    assert body["permission_denied_count"] >= 1
    assert "normal_user" in body["permission_denied_by_role"]
    assert "risk_level_distribution" in body
    assert "intent_distribution" in body

    denied = client.get("/api/admin/usage-stats?role=normal_user")
    assert denied.status_code == 403


def test_demo_permission_chain_sales_allowed_normal_user_denied_sop_allowed(client) -> None:
    sales = client.post(
        "/api/chat",
        json={
            "username": "demo_sales",
            "role": "sales",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    sales_body = sales.json()
    assert sales.status_code == 200
    assert sales_body["success"] is True
    assert sales_body["intent"] == "order_delivery_risk"

    denied = client.post(
        "/api/chat",
        json={
            "username": "demo_user",
            "role": "normal_user",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    denied_body = denied.json()
    assert denied.status_code == 200
    assert denied_body["success"] is False
    assert denied_body["risk_level"] == "blocked"
    assert any(
        row.get("step") == "permission" and row.get("permission_allowed") is False
        for row in denied_body["execution_trace"]
    )

    sop = client.post(
        "/api/chat",
        json={
            "username": "demo_user",
            "role": "normal_user",
            "question": "注塑件外观不良应该怎么处理？",
        },
    )
    sop_body = sop.json()
    assert sop.status_code == 200
    assert sop_body["success"] is True
    assert "query_exception_sop" in [tool["tool_name"] for tool in sop_body["called_tools"]]


def test_response_filter_role_rules_and_nested_data() -> None:
    payload = {
        "order_no": "O1001",
        "customer_name": "Customer A",
        "purchase_price": 12.5,
        "items": [
            {
                "sku_code": "SKU-KB-001",
                "cost": 3.2,
                "internal_note": "only for managers",
                "customer_phone": "13800000000",
            }
        ],
    }

    admin_payload, admin_changed = filter_response_by_role(payload, "admin")
    assert admin_changed is False
    assert admin_payload["purchase_price"] == 12.5

    normal_payload, normal_changed = filter_response_by_role(payload, "normal_user")
    assert normal_changed is True
    assert "purchase_price" not in normal_payload
    assert "customer_name" not in normal_payload

    sales_payload, sales_changed = filter_response_by_role(payload, "sales")
    assert sales_changed is True
    assert "purchase_price" not in sales_payload
    assert "cost" not in sales_payload["items"][0]
    assert "customer_name" in sales_payload

    warehouse_payload, warehouse_changed = filter_response_by_role(payload, "warehouse")
    assert warehouse_changed is True
    assert "customer_name" not in warehouse_payload
    assert "customer_phone" not in warehouse_payload["items"][0]

    missing_payload, missing_changed = filter_response_by_role({"sku_code": "SKU-KB-001"}, "sales")
    assert missing_changed is False
    assert missing_payload["sku_code"] == "SKU-KB-001"
