from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.auth import RolePermission


def _login(client, username: str, password: str = "demo123456") -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    return body["access_token"]


def test_login_and_me_returns_token_identity_and_permissions(client) -> None:
    token = _login(client, "demo_admin")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is True
    assert body["user"]["username"] == "demo_admin"
    assert body["user"]["role"] == "admin"
    assert "api:admin-usage-stats" in body["permissions"]
    assert "api:knowledge-rebuild" in body["permissions"]
    assert "menu:admin-dashboard" in body["permissions"]


def test_normal_user_menu_excludes_admin_entries(client) -> None:
    token = _login(client, "demo_user")

    response = client.get("/api/menus", headers={"Authorization": f"Bearer {token}"})
    body = response.json()

    assert response.status_code == 200
    menu_keys = {row["key"] for row in body["menus"]}
    assert "chat" in menu_keys
    assert "knowledge" in menu_keys
    assert "permissions" in menu_keys
    assert "dashboard" not in menu_keys
    assert "audit" not in menu_keys


def test_admin_menu_includes_dashboard_and_logs(client) -> None:
    token = _login(client, "demo_admin")

    response = client.get("/api/menus", headers={"Authorization": f"Bearer {token}"})
    body = response.json()

    assert response.status_code == 200
    menu_keys = {row["key"] for row in body["menus"]}
    assert {"dashboard", "audit", "approvals", "deployment"}.issubset(menu_keys)


def test_normal_user_token_denied_from_admin_api(client) -> None:
    token = _login(client, "demo_user")

    response = client.get(
        "/api/admin/usage-stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_sales_token_denied_from_admin_logs(client) -> None:
    token = _login(client, "demo_sales")

    response = client.get(
        "/api/admin/tool-call-logs",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["success"] is False


def test_admin_token_can_call_admin_api_without_role_query(client) -> None:
    token = _login(client, "demo_admin")

    response = client.get(
        "/api/admin/usage-stats",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_knowledge_rebuild_requires_specific_api_permission(client) -> None:
    token = _login(client, "demo_admin")

    allowed = client.post(
        "/api/knowledge/rebuild",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert allowed.status_code == 200

    with SessionLocal() as db:
        db.execute(
            delete(RolePermission).where(
                RolePermission.role_code == "admin",
                RolePermission.permission_code == "api:knowledge-rebuild",
            )
        )
        db.commit()

    denied = client.post(
        "/api/knowledge/rebuild",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert denied.status_code == 403
    assert denied.json()["success"] is False


def test_knowledge_search_role_denial_is_audited(client) -> None:
    response = client.get(
        "/api/knowledge/search",
        params={"query": "appearance defect", "role": "blocked_role"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is False
    assert body["permission_allowed"] is False

    logs = client.get("/api/admin/tool-call-logs?role=admin&limit=20")
    rows = logs.json()["data"]
    assert any(
        row["tool_name"] == "query_exception_sop"
        and row["permission_allowed"] is False
        for row in rows
    )


def test_knowledge_search_document_permission_denial_is_audited(client) -> None:
    token = _login(client, "demo_user")
    with SessionLocal() as db:
        db.execute(
            delete(RolePermission).where(
                RolePermission.role_code == "normal_user",
                RolePermission.permission_code == "document:sop-public",
            )
        )
        db.commit()

    response = client.get(
        "/api/knowledge/search",
        headers={"Authorization": f"Bearer {token}"},
        params={"query": "appearance defect"},
    )

    assert response.status_code == 403
    assert response.json()["success"] is False

    logs = client.get("/api/admin/tool-call-logs?role=admin&limit=20")
    rows = logs.json()["data"]
    assert any(
        row["tool_name"] == "query_exception_sop"
        and row["permission_allowed"] is False
        for row in rows
    )


def test_token_identity_overrides_forged_body_role(client) -> None:
    token = _login(client, "demo_user")

    response = client.post(
        "/api/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "demo_admin",
            "role": "admin",
            "question": "订单 O1001 现在能不能发货？",
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["success"] is False
    assert body["risk_level"] == "blocked"
    assert any(
        row.get("step") == "permission"
        and row.get("permission_allowed") is False
        for row in body["execution_trace"]
    )


def test_invalid_password_rejected(client) -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "demo_admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["success"] is False
