# CI / Observability Check Report

Date: 2026-06-25

## Boundary

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

## P13 Additions

- Added request id middleware.
- Added `request_id` to `agent_call_log` and `tool_call_log`.
- Added `/api/admin/metrics`.
- Added `scripts/run_ci_checks.py`.
- Added `.github/workflows/ci.yml` to run the same local CI gate on push and pull request.
- `scripts/run_ci_checks.py` uses workspace-local `.pytest-workspace-tmp/run-<pid>` for pytest and `.docker-config-tmp` for Docker config to avoid OS user-directory permission drift.
- Frontend already includes loading and error states for core views.

## Local CI Command

```bash
python scripts/run_ci_checks.py
```

Result: passed on 2026-06-25 with `VERIFY_DEPLOYMENT_BASE_URL=http://43.136.25.67`.

The script runs:

- `python -m compileall app`
- `python -m compileall scripts`
- `pytest -q --basetemp .pytest-tmp -p no:cacheprovider`
- `cd frontend && npm run test:smoke`
- `cd frontend && npm run build`
- `python scripts/package_cloud_deployment.py`
- `python scripts/verify_cloud_package.py`
- `python scripts/verify_cloud_report.py`
- `docker compose config`
- `python scripts/run_demo_report.py`
- `python scripts/run_rag_eval.py`

GitHub Actions entry:

```text
.github/workflows/ci.yml
```

The workflow installs backend dependencies, runs `npm ci` for the React console,
and then executes `python scripts/run_ci_checks.py`.

Production env validation is intentionally separate because `.env.production` should contain private values and is not committed:

```bash
python scripts/check_production_env.py --env-file .env.production
```

Optional deployment HTTP verification can be enabled when a local or cloud deployment is already running:

```bash
VERIFY_DEPLOYMENT_BASE_URL=http://localhost:8080 python scripts/run_ci_checks.py
```

`scripts/run_ci_checks.py` labels loopback deployment verification as `--environment local`; non-loopback URLs are labeled as `--environment cloud`.

On Windows PowerShell:

```powershell
$env:VERIFY_DEPLOYMENT_BASE_URL="http://localhost:8080"
python scripts/run_ci_checks.py
```

## Targeted Verification

```bash
pytest tests/test_p13_observability.py -q
```

Result: passed.

Full CI evidence from the latest run on 2026-06-25:

```text
python -m compileall app: passed
python -m compileall scripts: passed
pytest -q --basetemp .pytest-workspace-tmp/run-<pid> -p no:cacheprovider: 74 passed
frontend npm run test:smoke: 14 passed
frontend npm run build: passed
python scripts/package_cloud_deployment.py: wrote dist-cloud/manufacturing-ai-agent-cloud.zip plus .sha256 and .manifest.json
python scripts/verify_cloud_package.py: verified zip manifest, checksum, and exclusions
python scripts/verify_cloud_report.py: verified cloud report boundary status
docker compose config: passed
python scripts/run_demo_report.py: wrote docs/demo-report.md
python scripts/run_rag_eval.py: wrote docs/rag-eval-report.md
python scripts/verify_cloud_deployment.py --base-url http://43.136.25.67 --environment cloud: passed
```

Expected:

- `x-request-id` is returned in HTTP responses.
- Agent logs and tool logs include the same request id.
- `/api/admin/metrics` rejects non-admin users.
- `/api/admin/metrics` returns total requests, agent calls, tool calls, success rate, denied rate, average latency, and high risk count.
- React Chat Workbench renders answer, tool permissions, risk factors, manual review reason, and decision record.
- React Admin Dashboard loads both `/api/admin/usage-stats` and `/api/admin/metrics`.
- React shows a clear permission message when a page API returns 403.
- React Audit Logs loads agent/tool log lists and fetches `/api/admin/agent-call-logs/{id}` detail.
- React Knowledge Search renders SOP title, source path, score, and matched terms.
- React Deployment Status calls `/health` and shows demo/RAG report references.
- React normal_user can submit a platform permission request.
- React admin can approve pending platform permission requests.
- React returns to the login page with a clear message when an authenticated request receives 401.
- React shows the 404 page for unknown routes before login.
- Cloud deployment verifier checks the React SPA root page, `/health`, login, `/api/chat`, and admin dashboard read-only APIs.
- Permission approval API denials are written to `tool_call_log` with `permission_allowed=false`.
- Knowledge search role and document permission denials are written to `tool_call_log` with `permission_allowed=false`.

## Cloud Deployment Verification

P12 cloud verification completed on 2026-06-25 against Tencent Cloud Lighthouse:

```bash
python scripts/verify_cloud_deployment.py --base-url http://43.136.25.67 --environment cloud --write-report docs/cloud-deployment-check-report.md --timeout 20
python scripts/verify_cloud_report.py --report docs/cloud-deployment-check-report.md
```

Result: passed.

Verified HTTP surface:

- React SPA root served through Nginx.
- `/health` returned `status=ok` and `environment=production`.
- `/api/auth/login` worked for `demo_admin / demo123456`.
- `/api/chat` worked with bearer token and read-only tool calls.
- `/api/admin/usage-stats` and `/api/admin/metrics` worked with the admin token.

This is MVP cloud deployment verification with simulated ERP/MES/WMS data. It is not a production deployment claim or real enterprise system integration.
