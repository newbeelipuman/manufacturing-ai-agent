from __future__ import annotations

from typing import Any

from scripts import verify_cloud_deployment


def test_verify_cloud_deployment_checks_frontend_root(monkeypatch) -> None:
    def fake_request_json(
        base_url: str,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        timeout: int = 10,
    ) -> tuple[int, dict[str, Any]]:
        if path == "/health":
            return 200, {"status": "ok"}
        if path == "/api/auth/login":
            return 200, {"access_token": "token", "user": {"username": "demo_admin"}}
        if path == "/api/chat":
            return 200, {"success": True, "called_tools": [], "risk_level": "low"}
        if path == "/api/admin/usage-stats":
            return 200, {"total_calls": 1}
        if path == "/api/admin/metrics":
            return 200, {"total_requests": 1}
        raise AssertionError(path)

    def fake_request_text(
        base_url: str, path: str, timeout: int = 10
    ) -> tuple[int, str]:
        assert path == "/"
        return 200, '<title>Manufacturing AI Agent Console</title><div id="root"></div>'

    monkeypatch.setattr(verify_cloud_deployment, "request_json", fake_request_json)
    monkeypatch.setattr(verify_cloud_deployment, "request_text", fake_request_text)

    evidence = verify_cloud_deployment.verify("http://example.test", timeout=1)

    assert evidence["success"] is True
    assert evidence["checks"]["frontend"]["success"] is True
    assert evidence["checks"]["frontend"]["title_found"] is True
    assert evidence["checks"]["frontend"]["root_div_found"] is True
    assert evidence["checks"]["admin_dashboard"]["success"] is True


def test_verify_cloud_deployment_fails_when_frontend_root_missing(monkeypatch) -> None:
    def fake_request_json(
        base_url: str,
        path: str,
        method: str = "GET",
        payload: dict[str, Any] | None = None,
        token: str | None = None,
        timeout: int = 10,
    ) -> tuple[int, dict[str, Any]]:
        if path == "/health":
            return 200, {"status": "ok"}
        if path == "/api/auth/login":
            return 200, {"access_token": "token", "user": {"username": "demo_admin"}}
        if path == "/api/chat":
            return 200, {"success": True, "called_tools": [], "risk_level": "low"}
        if path == "/api/admin/usage-stats":
            return 200, {"total_calls": 1}
        if path == "/api/admin/metrics":
            return 200, {"total_requests": 1}
        raise AssertionError(path)

    def fake_request_text(
        base_url: str, path: str, timeout: int = 10
    ) -> tuple[int, str]:
        return 200, "not the react app"

    monkeypatch.setattr(verify_cloud_deployment, "request_json", fake_request_json)
    monkeypatch.setattr(verify_cloud_deployment, "request_text", fake_request_text)

    evidence = verify_cloud_deployment.verify("http://example.test", timeout=1)

    assert evidence["success"] is False
    assert evidence["checks"]["frontend"]["success"] is False


def test_cloud_environment_rejects_loopback_urls() -> None:
    assert verify_cloud_deployment.is_loopback_base_url("http://localhost:8080")
    assert verify_cloud_deployment.is_loopback_base_url("http://127.0.0.1:8080")
    assert verify_cloud_deployment.is_loopback_base_url("http://[::1]:8080")

    error = verify_cloud_deployment.environment_guard_error(
        "http://localhost:8080", "cloud"
    )

    assert error is not None
    assert "Refusing to write cloud evidence" in error
    assert (
        verify_cloud_deployment.environment_guard_error(
            "http://localhost:8080", "local"
        )
        is None
    )
    assert (
        verify_cloud_deployment.environment_guard_error(
            "http://203.0.113.10", "cloud"
        )
        is None
    )
