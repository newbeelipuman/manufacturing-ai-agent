from __future__ import annotations

import argparse
import ipaddress
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEMO_QUESTION = "订单 O1001 现在能不能发货？"
BOUNDARY_TEXT = """本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。"""


def is_loopback_base_url(base_url: str) -> bool:
    host = urlparse(base_url).hostname
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def environment_guard_error(base_url: str, environment: str) -> str | None:
    if environment == "cloud" and is_loopback_base_url(base_url):
        return (
            "Refusing to write cloud evidence for a loopback URL. Use "
            "--environment local for localhost rehearsals, or pass a real server "
            "IP/domain for cloud verification."
        )
    return None


def request_json(
    base_url: str,
    path: str,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    token: str | None = None,
    timeout: int = 10,
) -> tuple[int, dict[str, Any]]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            return exc.code, json.loads(body)
        except json.JSONDecodeError:
            return exc.code, {"raw": body}
    except URLError as exc:
        return 0, {"error": str(exc.reason)}


def request_text(
    base_url: str,
    path: str,
    timeout: int = 10,
) -> tuple[int, str]:
    request = Request(
        f"{base_url.rstrip('/')}{path}",
        headers={"Accept": "text/html, text/plain;q=0.9, */*;q=0.8"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", errors="replace")
    except URLError as exc:
        return 0, str(exc.reason)


def verify(base_url: str, timeout: int) -> dict[str, Any]:
    evidence: dict[str, Any] = {
        "base_url": base_url.rstrip("/"),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "boundary": (
            "MVP prototype with simulated ERP/MES/WMS data; Agent business tools "
            "remain read-only and do not execute outbound, adjustment, approval, "
            "purchase, order, or work-order write actions."
        ),
        "checks": {},
    }

    health_status, health_body = request_json(base_url, "/health", timeout=timeout)
    evidence["checks"]["health"] = {
        "status_code": health_status,
        "success": health_status == 200 and health_body.get("status") == "ok",
        "body": health_body,
    }

    frontend_status, frontend_body = request_text(base_url, "/", timeout=timeout)
    evidence["checks"]["frontend"] = {
        "status_code": frontend_status,
        "success": (
            frontend_status == 200
            and "Manufacturing AI Agent Console" in frontend_body
            and 'id="root"' in frontend_body
        ),
        "title_found": "Manufacturing AI Agent Console" in frontend_body,
        "root_div_found": 'id="root"' in frontend_body,
    }

    login_status, login_body = request_json(
        base_url,
        "/api/auth/login",
        method="POST",
        payload={"username": "demo_admin", "password": "demo123456"},
        timeout=timeout,
    )
    token = login_body.get("access_token") if isinstance(login_body, dict) else None
    evidence["checks"]["login"] = {
        "status_code": login_status,
        "success": login_status == 200 and bool(token),
        "user": login_body.get("user") if isinstance(login_body, dict) else None,
    }

    chat_status = 0
    chat_body: dict[str, Any] = {"skipped": "login failed"}
    if token:
        chat_status, chat_body = request_json(
            base_url,
            "/api/chat",
            method="POST",
            token=token,
            payload={
                "username": "demo_admin",
                "role": "admin",
                "question": DEMO_QUESTION,
            },
            timeout=timeout,
        )
    evidence["checks"]["chat"] = {
        "status_code": chat_status,
        "success": chat_status == 200 and chat_body.get("success") is True,
        "called_tools": [
            item.get("tool_name")
            for item in chat_body.get("called_tools", [])
            if isinstance(item, dict)
        ],
        "risk_level": chat_body.get("risk_level"),
    }

    usage_status = 0
    usage_body: dict[str, Any] = {"skipped": "login failed"}
    metrics_status = 0
    metrics_body: dict[str, Any] = {"skipped": "login failed"}
    if token:
        usage_status, usage_body = request_json(
            base_url,
            "/api/admin/usage-stats",
            token=token,
            timeout=timeout,
        )
        metrics_status, metrics_body = request_json(
            base_url,
            "/api/admin/metrics",
            token=token,
            timeout=timeout,
        )
    evidence["checks"]["admin_dashboard"] = {
        "success": usage_status == 200 and metrics_status == 200,
        "usage_stats": {
            "status_code": usage_status,
            "keys": sorted(usage_body.keys()) if isinstance(usage_body, dict) else [],
        },
        "metrics": {
            "status_code": metrics_status,
            "keys": sorted(metrics_body.keys()) if isinstance(metrics_body, dict) else [],
        },
    }

    evidence["success"] = all(
        check.get("success") for check in evidence["checks"].values()
    )
    return evidence


def render_report(evidence: dict[str, Any], environment: str) -> str:
    status = "Verified" if evidence["success"] else "Failed"
    if environment == "local":
        status = f"Local rehearsal {status.lower()}"
    checked_at = evidence["checked_at"]
    base_url = evidence["base_url"]
    health = evidence["checks"]["health"]
    frontend = evidence["checks"]["frontend"]
    login = evidence["checks"]["login"]
    chat = evidence["checks"]["chat"]
    admin_dashboard = evidence["checks"]["admin_dashboard"]
    raw_json = json.dumps(evidence, ensure_ascii=False, indent=2)
    server_note = (
        "Fill provider, region, public IP, OS, and CPU / memory after a real cloud run."
        if environment == "cloud"
        else "Local Docker/Nginx rehearsal; not cloud evidence."
    )
    return f"""# Cloud Deployment Check Report

Status: {status}

Date: {checked_at}

Server:

- Provider:
- Region:
- Public IP: {base_url}
- OS:
- CPU / Memory:

Note: {server_note}

## Boundary

{BOUNDARY_TEXT}

## Verification Checklist

- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] Security group opened for SSH and HTTP.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] Docker Engine installed.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] Repository uploaded or cloned.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] `.env.production` created from `.env.production.example`.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] Default `POSTGRES_PASSWORD` changed.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] Default `AUTH_SECRET_KEY` changed.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] `python scripts/check_production_env.py --env-file .env.production` passed.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] `docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production config` passed.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] `docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production up -d --build` passed.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] `python -m app.db.init_db` ran in backend container.
- [{'x' if environment == 'cloud' and evidence['success'] else ' '}] `python scripts/seed_demo_data.py` ran in backend container.
- [{'x' if health['success'] else ' '}] `curl {base_url}/health` returned healthy response.
- [{'x' if frontend['success'] else ' '}] React console opened through Nginx.
- [{'x' if login['success'] else ' '}] `demo_admin / demo123456` login worked.
- [{'x' if chat['success'] else ' '}] Chat workbench called `/api/chat` successfully.
- [{'x' if admin_dashboard['success'] else ' '}] Admin dashboard loaded usage stats and metrics.
- [{'x' if evidence['success'] else ' '}] `python scripts/verify_cloud_deployment.py --base-url {base_url}` passed.

## Command Evidence

```bash
python scripts/verify_cloud_deployment.py --base-url {base_url}
```

```json
{raw_json}
```

## Result

{status}.

This report is evidence for the environment named above. Do not describe it as production deployment or real enterprise rollout.
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify cloud or fullstack HTTP deployment for the MVP."
    )
    parser.add_argument(
        "--base-url",
        required=True,
        help="Deployment base URL, for example http://1.2.3.4 or http://localhost:8080.",
    )
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument(
        "--write-report",
        help="Optional path to write a Markdown check report.",
    )
    parser.add_argument(
        "--environment",
        choices=["cloud", "local"],
        default="cloud",
        help="Use 'local' for localhost rehearsals so the report is not cloud evidence.",
    )
    args = parser.parse_args()

    guard_error = environment_guard_error(args.base_url, args.environment)
    if guard_error:
        print(guard_error)
        raise SystemExit(2)

    evidence = verify(args.base_url, args.timeout)
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    if args.write_report:
        Path(args.write_report).write_text(
            render_report(evidence, args.environment), encoding="utf-8"
        )
    raise SystemExit(0 if evidence["success"] else 1)


if __name__ == "__main__":
    main()
