def _login(client, username: str = "demo_admin") -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "demo123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


from app.main import _json_safe_error_detail


def test_request_id_connects_response_agent_log_and_tool_log(client) -> None:
    request_id = "test-request-id-p13"
    response = client.post(
        "/api/chat",
        headers={"x-request-id": request_id},
        json={
            "username": "demo_admin",
            "role": "admin",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    assert response.status_code == 200
    assert response.headers["x-request-id"] == request_id

    agent_logs = client.get("/api/admin/agent-call-logs?role=admin&limit=20")
    tool_logs = client.get("/api/admin/tool-call-logs?role=admin&limit=50")

    assert any(row["request_id"] == request_id for row in agent_logs.json()["data"])
    assert any(row["request_id"] == request_id for row in tool_logs.json()["data"])

    tool_log_id = tool_logs.json()["data"][0]["id"]
    tool_detail = client.get(f"/api/admin/tool-call-logs/{tool_log_id}?role=admin")
    assert tool_detail.status_code == 200
    detail_body = tool_detail.json()
    assert detail_body["id"] == tool_log_id
    assert "tool_args_json" in detail_body
    assert "permission_allowed" in detail_body


def test_admin_audit_logs_support_filters(client) -> None:
    request_id = "test-request-id-filter-p13"
    response = client.post(
        "/api/chat",
        headers={"x-request-id": request_id},
        json={
            "username": "demo_admin",
            "role": "admin",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    assert response.status_code == 200

    agent_logs = client.get(
        "/api/admin/agent-call-logs",
        params={
            "role": "admin",
            "request_id": request_id,
            "username": "demo_admin",
            "log_role": "admin",
            "intent": "order_delivery_risk",
            "success": True,
        },
    )
    assert agent_logs.status_code == 200
    assert agent_logs.json()["data"]
    assert all(row["request_id"] == request_id for row in agent_logs.json()["data"])

    tool_logs = client.get(
        "/api/admin/tool-call-logs",
        params={
            "role": "admin",
            "request_id": request_id,
            "username": "demo_admin",
            "log_role": "admin",
            "tool_name": "query_order_status",
            "permission_allowed": True,
            "success": True,
        },
    )
    assert tool_logs.status_code == 200
    assert tool_logs.json()["data"]
    assert all(row["request_id"] == request_id for row in tool_logs.json()["data"])
    assert all(row["tool_name"] == "query_order_status" for row in tool_logs.json()["data"])


def test_chat_accepts_json_body_without_content_type(client) -> None:
    response = client.post(
        "/api/chat",
        content='{"username":"demo_admin","role":"admin","question":"订单 O1001 现在能不能发货？"}',
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_chat_accepts_json_string_body(client) -> None:
    response = client.post(
        "/api/chat",
        json='{"username":"demo_admin","role":"admin","question":"订单 O1001 现在能不能发货？"}',
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_admin_metrics_requires_admin_and_returns_summary(client) -> None:
    admin_token = _login(client, "demo_admin")
    user_token = _login(client, "demo_user")

    denied = client.get(
        "/api/admin/metrics",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert denied.status_code == 403

    allowed = client.get(
        "/api/admin/metrics",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    body = allowed.json()
    assert allowed.status_code == 200
    assert body["success"] is True
    assert "total_requests" in body
    assert "total_agent_calls" in body
    assert "total_tool_calls" in body
    assert "success_rate" in body
    assert "denied_rate" in body
    assert "avg_latency_ms" in body
    assert "high_risk_count" in body


def test_invalid_request_body_does_not_return_500(client) -> None:
    response = client.post(
        "/api/chat",
        content=b'{"question": "\xff"',
        headers={"Content-Type": "application/json"},
    )
    body = response.json()

    assert response.status_code in {400, 422}
    assert body["success"] is False


def test_validation_error_details_are_json_safe() -> None:
    detail = _json_safe_error_detail(
        [{"loc": ("body",), "input": b'{"question": "\xff"'}]
    )

    assert detail == [{"loc": ["body"], "input": '{"question": "�"'}]
