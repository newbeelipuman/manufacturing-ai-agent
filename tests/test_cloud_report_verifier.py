from __future__ import annotations

from scripts import verify_cloud_report


def _template_report() -> str:
    return "\n".join(
        [
            "# Cloud Deployment Check Report",
            "",
            "Status: Not executed yet",
            "",
            "## Boundary",
            "",
            *verify_cloud_report.BOUNDARY_LINES,
            "",
            "## Result",
            "",
            "Not yet verified on a real cloud server.",
        ]
    )


def _verified_report(public_ip: str) -> str:
    return f"""# Cloud Deployment Check Report

Status: Verified

Server:

- Provider: demo
- Region: demo
- Public IP: {public_ip}
- OS: Ubuntu 22.04
- CPU / Memory: 2C4G

## Boundary

{verify_cloud_report.BOUNDARY_LINES[0]}
{verify_cloud_report.BOUNDARY_LINES[1]}
{verify_cloud_report.BOUNDARY_LINES[2]}

```json
{{
  "success": true,
  "checks": {{
    "frontend": {{"success": true}},
    "health": {{"success": true}},
    "login": {{"success": true}},
    "chat": {{"success": true}},
    "admin_dashboard": {{"success": true}}
  }}
}}
```
"""


def test_cloud_report_template_is_boundary_safe() -> None:
    assert verify_cloud_report.validate_cloud_report_text(_template_report()) == []


def test_cloud_report_rejects_local_rehearsal_in_cloud_report() -> None:
    text = _template_report().replace(
        "Status: Not executed yet", "Status: Local rehearsal verified"
    )

    errors = verify_cloud_report.validate_cloud_report_text(text)

    assert any("Local rehearsal reports" in error for error in errors)


def test_cloud_report_rejects_verified_loopback_public_ip() -> None:
    errors = verify_cloud_report.validate_cloud_report_text(
        _verified_report("http://127.0.0.1:8080")
    )

    assert any("must not be loopback" in error for error in errors)


def test_cloud_report_accepts_verified_non_loopback_with_required_checks() -> None:
    errors = verify_cloud_report.validate_cloud_report_text(
        _verified_report("http://203.0.113.10")
    )

    assert errors == []


def test_cloud_report_rejects_forbidden_claims() -> None:
    text = _template_report() + "\n生产级上线\n"

    errors = verify_cloud_report.validate_cloud_report_text(text)

    assert any("Forbidden claim" in error for error in errors)
