from __future__ import annotations

import argparse
import ipaddress
import re
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_REPORT = Path("docs/cloud-deployment-check-report.md")
BOUNDARY_LINES = [
    "本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。",
    "Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。",
    "后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。",
]
FORBIDDEN_CLAIMS = [
    "生产级上线",
    "真实企业部署",
    "真实 ERP 接入",
    "企业客户已使用",
]
REQUIRED_VERIFIED_CHECKS = [
    '"frontend":',
    '"health":',
    '"login":',
    '"chat":',
    '"admin_dashboard":',
]


def _host_is_loopback(value: str) -> bool:
    candidate = value.strip()
    if not candidate:
        return False
    parsed = urlparse(candidate if "://" in candidate else f"http://{candidate}")
    host = parsed.hostname or candidate
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _extract_public_ip(text: str) -> str:
    match = re.search(r"^- Public IP:\s*(.+)$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def validate_cloud_report_text(text: str) -> list[str]:
    errors: list[str] = []
    for line in BOUNDARY_LINES:
        if line not in text:
            errors.append(f"Missing boundary line: {line}")
    for claim in FORBIDDEN_CLAIMS:
        if claim in text:
            errors.append(f"Forbidden claim found: {claim}")

    status_match = re.search(r"^Status:\s*(.+)$", text, re.MULTILINE)
    status = status_match.group(1).strip() if status_match else ""
    if not status:
        errors.append("Missing Status line.")
        return errors

    if status == "Not executed yet":
        if "Not yet verified on a real cloud server." not in text:
            errors.append("Template report must state that real cloud verification is not done.")
        return errors

    if status.lower().startswith("local rehearsal"):
        errors.append("Local rehearsal reports must not be written to the cloud check report.")
        return errors

    if status != "Verified":
        errors.append(f"Unexpected cloud report status: {status}")
        return errors

    public_ip = _extract_public_ip(text)
    if not public_ip or public_ip == "<server-ip>":
        errors.append("Verified cloud report must include a real Public IP or domain.")
    elif _host_is_loopback(public_ip):
        errors.append("Verified cloud report Public IP/domain must not be loopback.")

    if '"success": true' not in text:
        errors.append("Verified cloud report must include successful verifier JSON.")
    for check in REQUIRED_VERIFIED_CHECKS:
        if check not in text:
            errors.append(f"Verified cloud report missing verifier check: {check}")
    return errors


def validate_cloud_report(path: Path = DEFAULT_REPORT) -> list[str]:
    if not path.exists():
        return [f"Cloud report does not exist: {path}"]
    return validate_cloud_report_text(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate that the cloud deployment check report is boundary-safe."
    )
    parser.add_argument("--report", default=str(DEFAULT_REPORT))
    args = parser.parse_args()

    errors = validate_cloud_report(Path(args.report))
    if errors:
        for error in errors:
            print(error)
        raise SystemExit(1)
    print(f"Cloud report is boundary-safe: {args.report}")


if __name__ == "__main__":
    main()
