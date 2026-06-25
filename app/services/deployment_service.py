from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from app.core.config import settings


ROOT_DIR = Path(__file__).resolve().parents[2]
ALLOWED_SERVICES = {"backend", "nginx", "postgres", "redis"}
ALLOWED_REPORTS = {
    "cloud-deployment-check-report": {
        "label": "cloud deployment report",
        "path": "docs/cloud-deployment-check-report.md",
    },
    "demo-report": {
        "label": "demo report",
        "path": "docs/demo-report.md",
    },
}


def _run_readonly_docker_command(args: list[str], timeout: int = 5) -> dict[str, Any]:
    if shutil.which("docker") is None:
        return {
            "available": False,
            "stdout": "",
            "stderr": "docker command is not available in this runtime.",
            "returncode": None,
        }
    try:
        completed = subprocess.run(
            args,
            cwd=ROOT_DIR,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {
            "available": False,
            "stdout": "",
            "stderr": "docker command timed out.",
            "returncode": None,
        }
    return {
        "available": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def _compose_base_command() -> list[str]:
    command = ["docker", "compose", "-f", "docker-compose.yml"]
    if (ROOT_DIR / "docker-compose.cloud.yml").exists():
        command.extend(["-f", "docker-compose.cloud.yml"])
    return command


def _parse_compose_ps(output: str) -> list[dict[str, Any]]:
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    if not lines:
        return []
    parsed: list[dict[str, Any]] = []
    for line in lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, list):
            parsed.extend(item for item in value if isinstance(item, dict))
        elif isinstance(value, dict):
            parsed.append(value)
    return parsed


def get_deployment_status() -> dict[str, Any]:
    command = [*_compose_base_command(), "ps", "--format", "json"]
    result = _run_readonly_docker_command(command)
    services = []
    if result["available"]:
        for item in _parse_compose_ps(result["stdout"]):
            services.append(
                {
                    "name": item.get("Service") or item.get("Name") or "unknown",
                    "state": item.get("State") or item.get("Status") or "unknown",
                    "image": item.get("Image") or "",
                    "health": item.get("Health") or "",
                    "published_ports": item.get("Publishers") or item.get("Ports") or [],
                }
            )
    return {
        "success": True,
        "source": "docker_compose" if result["available"] else "runtime_fallback",
        "environment": settings.environment,
        "app": settings.app_name,
        "version": settings.app_version,
        "checked_at": datetime.utcnow().isoformat(),
        "services": services,
        "docker_available": result["available"],
        "message": result["stderr"] if not result["available"] else "Docker Compose status read.",
        "report_files": [
            {
                "id": report_id,
                "label": report["label"],
                "path": report["path"],
                "exists": (ROOT_DIR / report["path"]).exists(),
            }
            for report_id, report in ALLOWED_REPORTS.items()
        ],
    }


def get_deployment_logs(service: str, tail: int = 120) -> dict[str, Any]:
    if service not in ALLOWED_SERVICES:
        raise HTTPException(status_code=404, detail="Service log target not found.")
    safe_tail = min(max(tail, 20), 300)
    command = [*_compose_base_command(), "logs", "--tail", str(safe_tail), service]
    result = _run_readonly_docker_command(command, timeout=8)
    return {
        "success": True,
        "service": service,
        "source": "docker_compose_logs" if result["available"] else "runtime_fallback",
        "tail": safe_tail,
        "available": result["available"],
        "lines": result["stdout"].splitlines()[-safe_tail:] if result["stdout"] else [],
        "message": result["stderr"] if not result["available"] else "Docker Compose logs read.",
        "readonly_command": " ".join(command),
        "checked_at": datetime.utcnow().isoformat(),
    }


def get_deployment_report(report_id: str) -> dict[str, Any]:
    report = ALLOWED_REPORTS.get(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Deployment report target not found.")
    path = ROOT_DIR / report["path"]
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Deployment report file not found.")
    return {
        "success": True,
        "id": report_id,
        "label": report["label"],
        "path": report["path"],
        "content": path.read_text(encoding="utf-8"),
        "checked_at": datetime.utcnow().isoformat(),
    }
