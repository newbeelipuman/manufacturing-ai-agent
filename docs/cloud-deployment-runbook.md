# Cloud Deployment Runbook

## Boundary

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

## Target

Deploy the fullstack MVP to one Ubuntu server for demo verification:

- Nginx serves the React console.
- Nginx proxies `/api` and `/health` to FastAPI.
- FastAPI uses PostgreSQL for simulated business data.
- Redis is available for later platform use.

## Steps

1. Buy an Ubuntu 22.04 LTS or 24.04 LTS server.
2. Configure the security group:
   - SSH `22`.
   - HTTP `80`.
   - HTTPS `443` only when a domain/certificate is ready.
3. SSH to the server.
4. Install Docker Engine and the Compose plugin using Docker's official Ubuntu instructions.
5. Clone or upload this repository.

If Git clone is inconvenient, build the frontend locally and create a clean
upload package:

```bash
cd frontend
npm install
npm run build
cd ..
python scripts/package_cloud_deployment.py --output dist-cloud/manufacturing-ai-agent-cloud.zip
python scripts/verify_cloud_package.py --package dist-cloud/manufacturing-ai-agent-cloud.zip
```

Upload these files to the server:

- `dist-cloud/manufacturing-ai-agent-cloud.zip`
- `dist-cloud/manufacturing-ai-agent-cloud.zip.sha256`
- `dist-cloud/manufacturing-ai-agent-cloud.zip.manifest.json`

From Windows PowerShell, the shortest local upload/deploy path is:

```powershell
.\scripts\upload_and_deploy_cloud.ps1 -User ubuntu -ServerIp 43.136.25.67 -BaseUrl http://43.136.25.67
```

If Tencent Cloud uses another login user, replace `ubuntu` with that user. The
script uploads the package, runs the server-side deployment, and pulls
`docs/cloud-deployment-check-report.md` back to this workspace. Type passwords
only into the SSH/SCP prompts.

If a previous partial deployment initialized PostgreSQL with an old generated
password and the backend returns 502, reset only this disposable demo volume:

```powershell
.\scripts\upload_and_deploy_cloud.ps1 -User ubuntu -ServerIp 43.136.25.67 -BaseUrl http://43.136.25.67 -ResetDemoVolume
```

On the server, verify the uploaded zip before unzipping:

```bash
sha256sum -c manufacturing-ai-agent-cloud.zip.sha256
rm -rf manufacturing-ai-agent-cloud
mkdir -p manufacturing-ai-agent-cloud
unzip manufacturing-ai-agent-cloud.zip -d manufacturing-ai-agent-cloud
```

The package intentionally excludes local `.env` files, local SQLite databases,
Python caches, and `frontend/node_modules`.

After unzip, the scripted path is:

```bash
cd manufacturing-ai-agent-cloud
bash scripts/deploy_cloud_server.sh http://<server-ip>
```

The script creates `.env.production` with random server-side secrets, validates
it, starts Docker Compose with `docker-compose.cloud.yml`, initializes and seeds
the simulated MVP data, runs the HTTP verifier, and writes
`docs/cloud-deployment-check-report.md`. Keep using manual steps below when you
need to enter a fresh DeepSeek key or customize settings before startup.

### DeepSeek API 配置

DeepSeek Key 只放在服务器 `.env.production`，不要写进 React 前端、文档、GitHub 或聊天记录。若曾经把 Key 粘贴到聊天窗口，按已泄露处理：先在 DeepSeek 控制台作废旧 Key，再生成新 Key。

服务器上进入部署目录：

```bash
cd ~/manufacturing-ai-agent-cloud
nano .env.production
```

设置或修改这些变量：

```env
LLM_GATEWAY_MODE=deepseek
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
LLM_FALLBACK_MODEL=mock-safe-fallback
DEEPSEEK_API_KEY=<只在服务器输入的新 Key>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=20
```

保存后重启服务：

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production up -d --build
```

当前 DeepSeek 只接入 LLM Gateway 的路由与用量记录层；业务结论仍由后端只读工具、RBAC 权限校验和确定性回答组合生成，不会绕过权限，也不会执行出库、调账、审批、下单等写操作。

6. Create `.env.production` from `.env.production.example`.
7. Change at least:
   - `POSTGRES_PASSWORD`
   - `DATABASE_URL`
   - `AUTH_SECRET_KEY`
8. Validate production env values:

```bash
python scripts/check_production_env.py --env-file .env.production
```

The check rejects default demo secrets and SQLite production URLs.

9. Validate Compose configuration:

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production config
```

10. Build and start:

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production up -d --build
```

11. Initialize and seed simulated data:

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production exec backend python -m app.db.init_db
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production exec backend python scripts/seed_demo_data.py
```

12. Verify backend health:

```bash
curl http://<server-ip>/health
```

13. Open the frontend:

```text
http://<server-ip>/
```

14. Log in:

```text
demo_admin / demo123456
```

15. Verify `/api/chat` from the frontend Chat workbench with:

```text
订单 O1001 现在能不能发货？
```

16. Run the scripted HTTP verification:

```bash
python scripts/verify_cloud_deployment.py --base-url http://<server-ip>
```

The script checks:

- `GET /` for the React SPA shell served by Nginx
- `GET /health`
- `POST /api/auth/login`
- `POST /api/chat` with a bearer token
- `GET /api/admin/usage-stats` and `GET /api/admin/metrics` with the same bearer token

17. Record outputs in `docs/cloud-deployment-check-report.md`.

Or write the report directly after a real cloud run:

```bash
python scripts/verify_cloud_deployment.py \
  --base-url http://<server-ip> \
  --environment cloud \
  --write-report docs/cloud-deployment-check-report.md
```

Local rehearsal before buying or using a cloud server:

```bash
python scripts/verify_cloud_deployment.py --base-url http://localhost:8080 --environment local
```

Loopback URLs such as `localhost`, `127.0.0.1`, and `::1` are local rehearsal evidence only. The verifier refuses to label them as `--environment cloud`. If writing a local rehearsal report, keep it separate from the cloud report:

```bash
python scripts/verify_cloud_deployment.py \
  --base-url http://localhost:8080 \
  --environment local \
  --write-report docs/local-fullstack-deployment-check-report.md
```

## Rollback

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production down
```

To remove demo data volumes:

```bash
docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production down -v
```

Use volume deletion only for disposable demo environments.
