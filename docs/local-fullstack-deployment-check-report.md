# Local Fullstack Deployment Check Report

Date: 2026-06-24

## Boundary

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

## P11 Changes

- Added React static hosting through `docker/nginx.Dockerfile`; it copies the locally built `frontend/dist` into Nginx.
- Updated `docker/nginx.conf` to serve the SPA at `/`.
- Kept `/api/`, `/health`, `/docs`, and `/openapi.json` proxied to FastAPI.
- Updated `docker-compose.yml` so the `nginx` service builds the frontend image instead of using a plain Nginx image.
- Passed JWT settings through to the backend container.

## Local Verification

Run:

```bash
cd frontend
npm run build
```

Result: passed on 2026-06-24.

Evidence:

```text
vite v6.4.3 building for production...
✓ built
```

Run:

```bash
docker compose config
```

Result: passed on 2026-06-24. Compose rendered `backend`, `nginx`, `postgres`, and `redis`.

Runtime verification:

```bash
docker compose up -d --build
docker compose exec backend python -m app.db.init_db
docker compose exec backend python scripts/seed_demo_data.py
curl http://localhost:8080/health
```

Result: passed on 2026-06-24.

- `http://localhost:8080` serves the React console.
- `http://localhost:8080/health` returns backend health status.
- Login works with `demo_admin / demo123456`.
- Chat workbench calls `/api/chat` through Nginx.

Health evidence:

```json
{"status":"ok","app":"manufacturing-ai-agent","version":"0.1.0","environment":"docker"}
```

Container evidence:

```text
backend  Up  0.0.0.0:8000->8000/tcp
nginx    Up  0.0.0.0:8080->80/tcp
postgres Up  healthy 0.0.0.0:5432->5432/tcp
redis    Up  0.0.0.0:6379->6379/tcp
```

API evidence:

```text
POST http://localhost:8080/api/auth/login returned success=true and a bearer token.
POST http://localhost:8080/api/chat with the bearer token returned success=true.
```

## Notes

This report is deployment verification evidence for a local Docker/Nginx fullstack demo. It is not a production deployment claim and does not indicate real ERP/MES/WMS integration.
