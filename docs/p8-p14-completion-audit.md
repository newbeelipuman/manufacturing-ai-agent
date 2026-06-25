# P8-P14 Completion Audit

Date: 2026-06-25

Boundary:

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

This audit uses `docs/nuobida-fullstack-saas-next-phase-plan.md` as the execution baseline. It records local verification and the completed cloud-server MVP deployment verification.

## Summary

| Phase | Status | Evidence |
| --- | --- | --- |
| P8 React fullstack console | Locally verified | `frontend/`, `frontend/src/App.tsx`, `frontend/src/App.smoke.test.tsx`, `npm run test:smoke`, `npm run build`, README P8 section |
| P9 JWT/RBAC | Locally verified | `app/models/auth.py`, `app/services/auth_service.py`, `app/api/routes_auth.py`, `tests/test_p9_auth_rbac.py`, README P9 section |
| P10 permission request approval | Locally verified | `app/models/permission_request.py`, `app/services/permission_request_service.py`, `app/api/routes_permissions.py`, `tests/test_p10_permission_requests.py`, React smoke tests |
| P11 local Docker/Nginx fullstack | Locally verified | `docker/nginx.conf`, `docker/nginx.Dockerfile`, `docker-compose.yml`, `docs/local-fullstack-deployment-check-report.md`, `docker compose config` |
| P12 cloud server deployment | Cloud verified | `docs/cloud-deployment-check-report.md`, `scripts/verify_cloud_deployment.py`, `scripts/verify_cloud_report.py`, Tencent Cloud Lighthouse `http://43.136.25.67` |
| P13 CI/observability | Locally verified | `scripts/run_ci_checks.py`, `.github/workflows/ci.yml`, `tests/test_p13_observability.py`, `/api/admin/metrics`, request id middleware, frontend smoke tests |
| P14 resume/interview material | Locally verified | `docs/resume-project-bullets-nuobida.md`, `docs/interview-answer-nuobida.md`, `docs/interview-walkthrough.md`, README |

## P8 React Fullstack Console

Verified locally:

- React + TypeScript + Vite app exists under `frontend/`.
- Login page obtains JWT through `/api/auth/login`.
- Chat Workbench calls `/api/chat` and renders answer, called tools, permission results, risk factors, manual review reason, and decision record.
- Admin Dashboard renders usage stats and `/api/admin/metrics`.
- Audit Logs renders agent/tool logs and fetches `/api/admin/agent-call-logs/{id}` detail.
- Knowledge Search renders SOP title, source path, score, and matched terms.
- Permission Center renders current permissions, submits permission requests, and displays request history.
- Admin Approval Center loads pending requests and supports approve/reject UI.
- Deployment Status calls `/health` and shows demo/RAG report references.
- Frontend smoke tests cover RBAC menus, chat response rendering, metrics, audit detail, knowledge search, permission request/approval, missing chat menu, 401 token expiry, 403 permission prompt, deployment health, and 404 page.

Current verification:

```text
cd frontend && npm run test:smoke
14 passed

cd frontend && npm run build
passed
```

## P9 JWT/RBAC

Verified locally:

- Auth/RBAC models include user, role, permission, role permission, user role, user permission grant, menu/API/document permissions.
- Auth APIs include login, me, permissions, and menus.
- Frontend prefers bearer token identity.
- Backend keeps legacy role query/body compatibility for old demo tests.
- When token and role parameter are both present, backend resolves token identity first.
- Admin APIs, knowledge rebuild, knowledge search, and tool calls re-check backend permissions.
- Menu, API, document, and Agent tool permissions are covered by tests.

Current verification:

```text
pytest tests/test_p9_auth_rbac.py -q
covered by pytest with workspace-local `.pytest-tmp` and disabled pytest cacheprovider in scripts/run_ci_checks.py
```

## P10 Permission Request Approval

Verified locally:

- `PermissionRequest` model and APIs exist.
- Normal user can submit a platform permission request.
- User can list own request history.
- Admin can list pending requests and approve/reject.
- Approval grants platform access permission, not business approval.
- Rejection does not grant access.
- Request and approval actions write audit entries to `tool_call_log`.
- Denied admin approval attempts are audited with `permission_allowed=false`.
- React smoke tests cover normal-user request submission and admin approval UI.

Important boundary:

- This workflow approves platform permissions only.
- It does not approve, submit, dispatch, issue, adjust, or write ERP/MES/WMS business data.

## P11 Local Docker/Nginx Fullstack

Verified locally/prepared:

- `npm run build` produces `frontend/dist`.
- Nginx Docker image copies `frontend/dist`.
- Nginx serves React SPA and proxies `/api/`, `/health`, `/docs`, and `/openapi.json` to FastAPI.
- Docker Compose includes nginx, backend, postgres, and redis.
- Local deployment report exists at `docs/local-fullstack-deployment-check-report.md`.

Current verification:

```text
docker compose config
passed
```

## P12 Cloud Server Deployment

Cloud verified:

- Tencent Cloud Lighthouse server at `http://43.136.25.67`.
- OS: Ubuntu 24.04 LTS.
- CPU / memory: 2 cores / 4 GB.
- Docker Engine and Docker Compose were used to run the fullstack MVP.
- `docker-compose.cloud.yml` exposes only Nginx on port 80; PostgreSQL, Redis, and backend are not published to the public host.
- Nginx serves the React SPA and proxies FastAPI routes.
- FastAPI `/health` returned `status=ok` with `environment=production`.
- `demo_admin / demo123456` login returned a bearer token.
- `/api/chat` worked with the bearer token and called read-only Agent tools.
- `/api/admin/usage-stats` and `/api/admin/metrics` returned successfully with the admin token.
- `docs/cloud-deployment-check-report.md` is populated with successful verifier JSON.
- `python scripts/verify_cloud_report.py --report docs/cloud-deployment-check-report.md` passed.

Prepared artifacts:

- Cloud buying guide: `docs/cloud-server-buying-guide.md`.
- Cloud deployment runbook: `docs/cloud-deployment-runbook.md`.
- Cloud check report template: `docs/cloud-deployment-check-report.md`.
- HTTP verification script: `scripts/verify_cloud_deployment.py`.
- Production environment checker: `scripts/check_production_env.py`.
- Upload package builder: `scripts/package_cloud_deployment.py`.
- Upload package verifier: `scripts/verify_cloud_package.py`.
- Cloud zip artifact: `dist-cloud/manufacturing-ai-agent-cloud.zip`.
- Package checksum: `dist-cloud/manufacturing-ai-agent-cloud.zip.sha256`.
- Package manifest: `dist-cloud/manufacturing-ai-agent-cloud.zip.manifest.json`.

Verified locally and by cloud HTTP checks:

- Cloud package excludes `.env`, `.env.production`, `node_modules`, local DBs, and `dist-cloud`.
- Package includes runtime source, Docker files, frontend dist, docs, scripts, and tests.
- Package metadata records SHA-256, file count, excluded paths, and the prepared-only cloud status.
- `tests/test_cloud_package.py` covers package inclusion/exclusion rules, metadata checksum generation, and tamper detection.
- `scripts/verify_cloud_package.py` verifies an existing zip against its manifest, checksum, and exclusion rules.
- `scripts/verify_cloud_report.py` verifies that the cloud report keeps boundary wording, rejects forbidden deployment claims, and does not label local rehearsal evidence as cloud evidence.
- `scripts/verify_cloud_deployment.py` checks `/`, `/health`, `/api/auth/login`, `/api/chat`, `/api/admin/usage-stats`, and `/api/admin/metrics`.
- `scripts/verify_cloud_deployment.py` refuses to label loopback URLs such as `localhost`, `127.0.0.1`, or `::1` as cloud evidence.
- README documents the same cloud verification scope, including the Nginx-served React SPA root page, bearer-token `/api/chat`, and admin dashboard read-only APIs.
- `tests/test_cloud_deployment_verifier.py` covers the frontend-root check in the deployment verifier.

Cloud verification evidence:

```text
curl http://43.136.25.67/health
python scripts/verify_cloud_deployment.py --base-url http://43.136.25.67 --environment cloud --write-report docs/cloud-deployment-check-report.md
python scripts/verify_cloud_report.py --report docs/cloud-deployment-check-report.md
```

The cloud run is MVP deployment verification only. It is not production deployment, real enterprise rollout, real ERP/MES/WMS integration, or customer usage.

## P13 CI And Observability

Verified locally:

- `scripts/run_ci_checks.py` runs backend compile, script compile, pytest with workspace-local `.pytest-tmp`, frontend smoke, frontend build, cloud package, cloud package verification, compose config with workspace-local Docker config, demo report, and RAG eval.
- `.github/workflows/ci.yml` runs the same local CI script.
- Request ID middleware returns `x-request-id`.
- `agent_call_log.request_id` and `tool_call_log.request_id` persist request IDs.
- `/api/admin/metrics` returns total requests, agent calls, tool calls, success rate, denied rate, average latency, and high risk count.
- Tests cover request id correlation and metrics access.
- Frontend quality coverage includes loading states, error messages, 401 token expiry, 403 permission prompts, and 404 page.

Current verification:

```text
python scripts/run_ci_checks.py
passed on 2026-06-24

Included checks:
- python -m compileall app
- python -m compileall scripts
- pytest -q --basetemp .pytest-tmp -p no:cacheprovider: 74 passed
- frontend npm run test:smoke: 14 passed
- frontend npm run build
- python scripts/package_cloud_deployment.py
- python scripts/verify_cloud_package.py
- python scripts/verify_cloud_report.py
- docker compose config
- python scripts/run_demo_report.py
- python scripts/run_rag_eval.py
```

The latest recorded CI evidence is maintained in `docs/ci-cd-check-report.md`.

## P14 Resume And Interview Materials

Verified locally:

- `docs/resume-project-bullets-nuobida.md` describes the project as an MVP using simulated ERP/MES/WMS data.
- `docs/interview-answer-nuobida.md` explains Agent orchestration, RBAC, permission approval, frontend pages, CI/observability, Docker/Nginx, and cloud-preparation boundaries.
- `docs/interview-walkthrough.md` includes the read-only boundary and real-system replacement path.
- README includes startup, frontend, Docker/Nginx, P8-P14 evidence, and boundary wording.

Required wording retained:

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

## Current Conclusion

P8, P9, P10, P11, P13, and P14 are locally implemented and verified with tests, builds, scripts, and documentation.

P12 is complete for the MVP objective: a real Tencent Cloud server run verifies Nginx-served React, FastAPI health, JWT login, bearer-token `/api/chat`, and admin usage/metrics APIs, with evidence recorded in `docs/cloud-deployment-check-report.md`.
