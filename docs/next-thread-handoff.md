# Next Thread Handoff

Date: 2026-06-25

This handoff summarizes the current state of `G:\manufacturing-ai-agent` so the next Codex thread can continue without rereading the full prior conversation.

## Current Goal

Use `docs/nuobida-fullstack-saas-next-phase-plan.md` as the execution baseline to complete P8-P14:

- P8 React fullstack console
- P9 JWT/RBAC
- P10 permission request and approval
- P11 local Docker/Nginx fullstack
- P12 cloud server deployment preparation and real verification
- P13 CI/observability hardening
- P14 resume/interview material update

Preserve the core boundary:

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

## Completion Status

P8, P9, P10, P11, P13, and P14 are locally implemented and verified.

P12 is prepared but not complete. The user has now purchased a Tencent Cloud Lighthouse server, but real cloud deployment verification has not yet been executed.

Do not mark the goal complete until a real server run proves:

- Nginx serves the React SPA from the cloud server.
- `/health` works through the cloud server.
- `/api/auth/login` works.
- `/api/chat` works with bearer token.
- `/api/admin/usage-stats` and `/api/admin/metrics` work.
- The cloud deployment report is populated with real server evidence.

## Important P8-P14 Evidence

Known latest verification:

```text
python scripts\run_ci_checks.py: passed
pytest: 74 passed
frontend smoke: 14 passed
frontend build: passed
docker compose config: passed
cloud package verify: passed
cloud report verify: passed
```

The CI script now runs:

- `python -m compileall app`
- `python -m compileall scripts`
- `pytest -q --basetemp .pytest-tmp -p no:cacheprovider`
- `frontend npm run test:smoke`
- `frontend npm run build`
- `python scripts/package_cloud_deployment.py`
- `python scripts/verify_cloud_package.py`
- `python scripts/verify_cloud_report.py`
- `docker compose config`
- `python scripts/run_demo_report.py`
- `python scripts/run_rag_eval.py`

CI was hardened to use workspace-local temp/config directories:

- `.pytest-tmp`
- `.docker-config-tmp`

These are excluded by `.gitignore`, `.dockerignore`, and the cloud package builder.

## Cloud Package

Latest cloud package artifacts:

- `dist-cloud/manufacturing-ai-agent-cloud.zip`
- `dist-cloud/manufacturing-ai-agent-cloud.zip.manifest.json`
- `dist-cloud/manufacturing-ai-agent-cloud.zip.sha256`

The package verifier confirmed:

- SHA-256 matches manifest.
- `.env` and `.env.production` are excluded.
- `node_modules` is excluded.
- `dist-cloud` is excluded.
- `.pytest-tmp` and `.docker-config-tmp` are excluded.
- Runtime source, Docker/Nginx files, docs, scripts, tests, and `frontend/dist` are included.

## P12 Cloud Deployment Guardrails

Scripts added or hardened:

- `scripts/package_cloud_deployment.py`
- `scripts/verify_cloud_package.py`
- `scripts/verify_cloud_deployment.py`
- `scripts/verify_cloud_report.py`
- `scripts/check_production_env.py`

`scripts/verify_cloud_deployment.py` checks:

- `GET /` for the React SPA shell
- `GET /health`
- `POST /api/auth/login`
- `POST /api/chat` with bearer token
- `GET /api/admin/usage-stats`
- `GET /api/admin/metrics`

It refuses to label loopback URLs as cloud evidence. `localhost`, `127.0.0.1`, and `::1` must use `--environment local`, not `--environment cloud`.

`scripts/verify_cloud_report.py` validates that `docs/cloud-deployment-check-report.md`:

- Keeps required MVP/read-only boundary wording.
- Does not contain forbidden production claims.
- Does not treat local rehearsal as cloud evidence.
- If status is `Verified`, includes a non-loopback public IP/domain and successful verifier JSON.

Current `docs/cloud-deployment-check-report.md` is still a template and says real cloud verification has not been performed.

## Purchased Cloud Server

The user purchased a Tencent Cloud Lighthouse server on 2026-06-25.

Observed from the final screenshot:

```text
Cloud provider: Tencent Cloud
Product: Lighthouse / 轻量应用服务器
Server name: manufacturing-ai-agent
Status: running
Public IPv4: 43.136.25.67
CPU: 2 cores
Memory: 4GB
System disk: 60GB
OS: Ubuntu 24.04 LTS
Region: Guangzhou, inferred from purchase flow
Expires: 2027-06-25 01:03:47
```

The user used custom password login during purchase. Do not ask the user to paste the password into chat.

The purchased spec is enough for this MVP:

- Nginx + React static files
- FastAPI backend
- PostgreSQL
- Redis
- DeepSeek API calls through backend

No GPU is needed.

## Server Buying Context

The buying journey compared Tencent Cloud and Alibaba Cloud. The final decision was Tencent Cloud because the user wanted the stable 2C4G option instead of the cheaper but tighter 2C2G Alibaba Cloud plan.

Avoid revisiting provider selection unless the purchased server cannot be used.

Alibaba Cloud links given to user:

- `https://www.aliyun.com/product/swas`
- `https://www.aliyun.com/benefit/scene/swas`
- `https://www.aliyun.com/product/ecs`

The Alibaba Cloud free trial and cheaper 2C2G options were rejected or deprioritized because of image/spec limitations and tighter memory.

## Security Guidance Already Given

Public servers will be scanned. This is normal.

Tencent Cloud and Alibaba Cloud both provide basic DDoS/security protection, but they do not protect against weak passwords, leaked keys, exposed databases, or application bugs.

Deployment security rules:

- Open only 22 and 80 initially.
- Add 443 later if using domain/HTTPS.
- Do not expose PostgreSQL 5432 to the public internet.
- Do not expose Redis 6379 to the public internet.
- Use a strong SSH password or SSH key.
- Keep `.env.production` only on the server.
- Put `DEEPSEEK_API_KEY` only in server-side environment config.
- Never put API keys in React/frontend code.

## DeepSeek API Context

The user uses DeepSeek API.

No GPU server is needed because inference happens through DeepSeek API.

The project currently uses mock LLM Gateway for MVP demonstration. This was intentional because P8-P14 focus on fullstack Agent workflow, permissions, audit, RAG, Docker/Nginx, and deployment evidence.

Important secret-handling update from 2026-06-25:

- The user pasted a DeepSeek API key in chat during the prior thread.
- Treat that key as exposed and do not use it.
- Do not write the key value into any file, commit, documentation, cloud package, GitHub repository, or final answer.
- In the next deployment thread, tell the user to revoke/rotate that key in the DeepSeek console and create a fresh key.
- The fresh key must be entered only on the server in `.env.production` or through a secure server-side secret mechanism.

Once the server is bought, configure DeepSeek in `.env.production`, for example:

```env
LLM_PROVIDER=deepseek
LLM_GATEWAY_MODE=deepseek
DEEPSEEK_API_KEY=<user-provided-key-on-server-only>
```

Before assuming this works, inspect the current code for actual config names and DeepSeek support. If support is not implemented yet, add it carefully in the backend service layer without exposing the key to the frontend.

## What To Do Next In The New Thread

Start from the purchased Tencent Cloud server and continue P12. Do not ask again which cloud provider to buy.

Known safe deployment details:

```text
公网 IP: 43.136.25.67
系统版本: Ubuntu 24.04 LTS
服务商: 腾讯云轻量应用服务器
规格: 2核4G / 60GB
登录方式: 自定义密码, but password must not be pasted into chat
```

First ask the user to confirm whether security group / firewall ports 22 and 80 are open. If uncertain, guide them in Tencent Cloud console. Do not ask them to paste passwords or API keys into chat. Tell them to type secrets directly into SSH prompts or server-side `.env.production`.

Then continue P12:

1. Confirm Tencent Cloud firewall/security group allows inbound TCP 22 and 80.
2. SSH into server as `ubuntu@43.136.25.67`, or guide the user through Tencent Cloud web login if SSH is not ready.
3. Update apt packages.
4. Install Docker Engine and Docker Compose plugin.
5. Add the `ubuntu` user to the `docker` group if needed, or use `sudo docker`.
6. Upload or clone the project.
7. If not using Git, upload:
   - `dist-cloud/manufacturing-ai-agent-cloud.zip`
   - `dist-cloud/manufacturing-ai-agent-cloud.zip.sha256`
   - `dist-cloud/manufacturing-ai-agent-cloud.zip.manifest.json`
8. Verify package checksum on server with `sha256sum -c manufacturing-ai-agent-cloud.zip.sha256`.
9. Unzip package and enter the project directory.
10. Create `.env.production` from `.env.production.example`.
11. Configure secure database/auth passwords and DeepSeek API key server-side.
12. Run `python scripts/check_production_env.py --env-file .env.production`.
13. Run `docker compose --env-file .env.production config`.
14. Run `docker compose --env-file .env.production up -d --build`.
15. Initialize DB and seed simulated demo data.
16. Run:

```bash
python scripts/verify_cloud_deployment.py \
  --base-url http://43.136.25.67 \
  --environment cloud \
  --write-report docs/cloud-deployment-check-report.md
```

17. Run:

```bash
python scripts/verify_cloud_report.py --report docs/cloud-deployment-check-report.md
```

18. Update `docs/p8-p14-completion-audit.md` and `docs/ci-cd-check-report.md` with the real cloud evidence.
19. Re-run `python scripts/run_ci_checks.py` locally after pulling the updated report back, if feasible.

Suggested first commands after SSH:

```bash
whoami
uname -a
lsb_release -a
curl -I http://43.136.25.67 || true
```

Suggested Docker install route on Ubuntu 24.04:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg unzip
```

Then use the official Docker Engine install instructions for Ubuntu. If the next thread uses commands from memory, it should still verify them against Docker's official docs or Ubuntu package availability before making large changes.

## Important Caution For Next Thread

Do not claim:

- production deployment
- real enterprise deployment
- real ERP/MES/WMS integration
- customer usage
- fake efficiency or cost reduction metrics

The correct wording after a real cloud run is:

```text
使用云服务器完成 Docker Compose 部署验证，Nginx 托管 React 前端并反代 FastAPI API，PostgreSQL 持久化模拟业务数据，形成可复现部署文档和检查报告。
```

## Git Status Note

`git status` repeatedly failed with:

```text
fatal: not a git repository (or any of the parent directories): .git
```

The workspace files exist, but this directory currently does not expose a Git repository to the agent.

## 2026-06-25 Latest Update: Cloud Verified And P15 Product Optimization Next

The earlier sections in this file describe the state before real cloud verification. The latest state is:

- Tencent Cloud server `43.136.25.67` has been deployed and verified.
- `docs/cloud-deployment-check-report.md` now says `Status: Verified`.
- The deployment runs React through Nginx, FastAPI backend, PostgreSQL, and Redis through Docker Compose.
- The verifier passed for `/health`, frontend shell, login, `/api/chat`, `/api/admin/usage-stats`, and `/api/admin/metrics`.

The next thread should not restart cloud provider selection or basic P12 deployment unless a new deployment error appears.

Read these files before continuing:

- `docs/thread-2026-06-25-cloud-and-product-ux-summary.md`
- `docs/cloud-server-first-deployment-experience.md`
- `docs/p15-product-hardening-backlog.md`
- `docs/next-thread-product-optimization-prompt.md`

The user wants the next thread to focus on product hardening:

- Permission changes must have remarks and backend audit.
- Backend must distinguish `request_approval`, `admin_direct_change`, and `system_seed`.
- Approval center must require and persist approval reasons.
- Audit/admin pages should auto-refresh naturally when opened.
- Editable pages need draft preservation.
- Deployment center should become a useful read-only ops view with service status and logs.
- Chat UI needs history, FAQ, follow-up context, and business-readable Chinese output.

Important: during the last turn, small code changes were made for Chinese SOP miss text, Chinese shipment risk evidence, approval textarea, and `business_identifier_not_found` label fallback. The next thread should inspect and test these changes before building on them.
