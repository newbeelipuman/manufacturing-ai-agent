from sqlalchemy import delete

from app.db.session import SessionLocal
from app.models.auth import RolePermission


def _login(client, username: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "demo123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_normal_user_request_approved_grants_menu_permission(client) -> None:
    user_token = _login(client, "demo_user")
    admin_token = _login(client, "demo_admin")

    before = client.get("/api/menus", headers={"Authorization": f"Bearer {user_token}"})
    assert "dashboard" not in {row["key"] for row in before.json()["menus"]}

    submitted = client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:admin-dashboard",
            "reason": "需要查看 usage dashboard 以排查演示调用情况。",
        },
    )
    assert submitted.status_code == 200
    request_id = submitted.json()["data"]["id"]
    assert submitted.json()["data"]["status"] == "pending"

    pending = client.get(
        "/api/admin/permission-requests?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert pending.status_code == 200
    assert any(row["id"] == request_id for row in pending.json()["data"])

    approved = client.post(
        f"/api/admin/permission-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approval_comment": "仅用于查看平台 usage dashboard。"},
    )
    assert approved.status_code == 200
    assert approved.json()["data"]["status"] == "approved"

    after = client.get("/api/menus", headers={"Authorization": f"Bearer {user_token}"})
    assert "dashboard" in {row["key"] for row in after.json()["menus"]}

    logs = client.get("/api/admin/tool-call-logs?role=admin&limit=100")
    rows = logs.json()["data"]
    assert any(row["tool_name"] == "platform_permission_request" for row in rows)
    assert any(row["tool_name"] == "platform_permission_approval" for row in rows)


def test_rejected_permission_request_does_not_grant_permission(client) -> None:
    user_token = _login(client, "demo_user")
    admin_token = _login(client, "demo_admin")

    submitted = client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:audit-logs",
            "reason": "想查看审计日志。",
        },
    )
    request_id = submitted.json()["data"]["id"]

    rejected = client.post(
        f"/api/admin/permission-requests/{request_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approval_comment": "普通用户不开放审计日志。"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["data"]["status"] == "rejected"

    menus = client.get("/api/menus", headers={"Authorization": f"Bearer {user_token}"})
    assert "audit" not in {row["key"] for row in menus.json()["menus"]}


def test_non_admin_cannot_approve_permission_request(client) -> None:
    user_token = _login(client, "demo_user")
    sales_token = _login(client, "demo_sales")

    submitted = client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:admin-dashboard",
            "reason": "申请查看 dashboard。",
        },
    )
    request_id = submitted.json()["data"]["id"]

    denied = client.post(
        f"/api/admin/permission-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {sales_token}"},
        json={"approval_comment": "not allowed"},
    )
    assert denied.status_code == 403
    assert denied.json()["success"] is False


def test_admin_permission_request_api_requires_specific_api_permission(client) -> None:
    user_token = _login(client, "demo_user")
    admin_token = _login(client, "demo_admin")

    submitted = client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:admin-dashboard",
            "reason": "verify api-level rbac",
        },
    )
    request_id = submitted.json()["data"]["id"]

    with SessionLocal() as db:
        db.execute(
            delete(RolePermission).where(
                RolePermission.role_code == "admin",
                RolePermission.permission_code == "api:admin-permission-requests",
            )
        )
        db.commit()

    denied_list = client.get(
        "/api/admin/permission-requests?status=pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert denied_list.status_code == 403

    denied_approval = client.post(
        f"/api/admin/permission-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approval_comment": "should be denied by api permission"},
    )
    assert denied_approval.status_code == 403

    logs = client.get("/api/admin/tool-call-logs?role=admin&limit=100")
    rows = logs.json()["data"]
    denied_rows = [
        row
        for row in rows
        if row["tool_name"] == "platform_permission_approval"
        and row["permission_allowed"] is False
    ]
    assert len(denied_rows) >= 2


def test_my_permission_requests_returns_only_current_user(client) -> None:
    user_token = _login(client, "demo_user")
    sales_token = _login(client, "demo_sales")

    client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:admin-dashboard",
            "reason": "申请查看 dashboard。",
        },
    )

    mine = client.get(
        "/api/permissions/requests/my",
        headers={"Authorization": f"Bearer {sales_token}"},
    )
    assert mine.status_code == 200
    assert mine.json()["data"] == []


def test_permission_decision_requires_reason_and_writes_change_log(client) -> None:
    user_token = _login(client, "demo_user")
    admin_token = _login(client, "demo_admin")

    submitted = client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:admin-dashboard",
            "reason": "Need dashboard access for demo troubleshooting.",
        },
    )
    request_id = submitted.json()["data"]["id"]

    missing_reason = client.post(
        f"/api/admin/permission-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approval_comment": "   "},
    )
    assert missing_reason.status_code == 422

    approved = client.post(
        f"/api/admin/permission-requests/{request_id}/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approval_comment": "Reason checked by admin."},
    )
    assert approved.status_code == 200

    change_logs = client.get(
        "/api/admin/permission-change-logs",
        headers={"Authorization": f"Bearer {admin_token}"},
        params={
            "source": "request_approval",
            "operator_username": "demo_admin",
            "target_type": "user",
            "target_identifier": "demo_user",
            "permission_code": "menu:admin-dashboard",
            "request_id": request_id,
            "limit": 20,
        },
    )
    assert change_logs.status_code == 200
    assert any(
        row["request_id"] == request_id
        and row["source"] == "request_approval"
        and row["operator_username"] == "demo_admin"
        and row["target_identifier"] == "demo_user"
        and row["permission_code"] == "menu:admin-dashboard"
        and row["remark"] == "Reason checked by admin."
        for row in change_logs.json()["data"]
    )


def test_rejected_permission_request_writes_change_log(client) -> None:
    user_token = _login(client, "demo_user")
    admin_token = _login(client, "demo_admin")

    submitted = client.post(
        "/api/permissions/requests",
        headers={"Authorization": f"Bearer {user_token}"},
        json={
            "requested_permission": "menu:audit-logs",
            "reason": "Need audit page access.",
        },
    )
    request_id = submitted.json()["data"]["id"]

    rejected = client.post(
        f"/api/admin/permission-requests/{request_id}/reject",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"approval_comment": "Audit logs remain admin-only."},
    )
    assert rejected.status_code == 200

    change_logs = client.get(
        "/api/admin/permission-change-logs?source=request_approval&limit=20",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert any(
        row["request_id"] == request_id
        and row["diff"]["decision"] == "rejected"
        and row["remark"] == "Audit logs remain admin-only."
        for row in change_logs.json()["data"]
    )


def test_admin_direct_role_permission_change_requires_remark_and_logs(client) -> None:
    admin_token = _login(client, "demo_admin")

    before = client.get(
        "/api/admin/role-permissions/sales",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert before.status_code == 200
    before_permissions = before.json()["data"]["permissions"]
    assert "menu:audit-logs" not in before_permissions

    missing_remark = client.post(
        "/api/admin/role-permissions/sales",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"permission_codes": before_permissions + ["menu:audit-logs"], "remark": ""},
    )
    assert missing_remark.status_code == 422

    saved = client.post(
        "/api/admin/role-permissions/sales",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "permission_codes": before_permissions + ["menu:audit-logs"],
            "remark": "Admin direct role permission change for platform access verification.",
        },
    )
    assert saved.status_code == 200
    assert saved.json()["data"]["source"] == "admin_direct_change"
    assert "menu:audit-logs" in saved.json()["data"]["added"]

    change_logs = client.get(
        "/api/admin/permission-change-logs?source=admin_direct_change&target_identifier=sales",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert change_logs.status_code == 200
    assert any(
        row["source"] == "admin_direct_change"
        and row["operator_username"] == "demo_admin"
        and row["target_type"] == "role"
        and "menu:audit-logs" in row["diff"]["added"]
        and row["remark"] == "Admin direct role permission change for platform access verification."
        for row in change_logs.json()["data"]
    )
