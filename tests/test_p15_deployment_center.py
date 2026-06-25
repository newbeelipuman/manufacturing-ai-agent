from app.services import deployment_service


def _login(client, username: str) -> str:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": "demo123456"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_admin_can_read_deployment_status(client, monkeypatch) -> None:
    admin_token = _login(client, "demo_admin")

    monkeypatch.setattr(
        deployment_service,
        "_run_readonly_docker_command",
        lambda args, timeout=5: {
            "available": True,
            "stdout": '{"Service":"backend","State":"running","Image":"backend:test"}\n',
            "stderr": "",
            "returncode": 0,
        },
    )

    response = client.get(
        "/api/admin/deployment/status",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "docker_compose"
    assert body["services"][0]["name"] == "backend"
    assert body["services"][0]["state"] == "running"


def test_admin_can_read_whitelisted_deployment_logs(client, monkeypatch) -> None:
    admin_token = _login(client, "demo_admin")

    monkeypatch.setattr(
        deployment_service,
        "_run_readonly_docker_command",
        lambda args, timeout=8: {
            "available": True,
            "stdout": "backend line 1\nbackend line 2\n",
            "stderr": "",
            "returncode": 0,
        },
    )

    response = client.get(
        "/api/admin/deployment/logs/backend?tail=20",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "backend"
    assert body["available"] is True
    assert body["lines"] == ["backend line 1", "backend line 2"]
    assert "logs --tail 20 backend" in body["readonly_command"]


def test_admin_can_read_whitelisted_deployment_report(client) -> None:
    admin_token = _login(client, "demo_admin")

    response = client.get(
        "/api/admin/deployment/reports/demo-report",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == "demo-report"
    assert body["path"] == "docs/demo-report.md"
    assert body["content"]


def test_deployment_report_rejects_unknown_file(client) -> None:
    admin_token = _login(client, "demo_admin")

    response = client.get(
        "/api/admin/deployment/reports/../../README.md",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


def test_deployment_logs_reject_unknown_service(client) -> None:
    admin_token = _login(client, "demo_admin")

    response = client.get(
        "/api/admin/deployment/logs/unknown?tail=20",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 404


def test_non_admin_cannot_read_deployment_status(client) -> None:
    user_token = _login(client, "demo_user")

    response = client.get(
        "/api/admin/deployment/status",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert response.status_code == 403
