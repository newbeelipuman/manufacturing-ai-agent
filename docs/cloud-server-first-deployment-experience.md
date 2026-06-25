# 第一次云服务器选型与部署经验

日期：2026-06-25

本文专门记录第一次为 `manufacturing-ai-agent` 购买、配置、部署和调试云服务器的过程。后续如果没有错误或明确架构调整，只做增量追加，不整体重写，保留踩坑轨迹。

## 项目边界

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

## 选型过程

本次主要比较了阿里云轻量应用服务器、阿里云 ECS 和腾讯云轻量应用服务器。

最终选择：

- 云厂商：腾讯云
- 产品：轻量应用服务器
- 公网 IP：`43.136.25.67`
- 系统：Ubuntu 24.04 LTS
- 规格：2 核 4G / 60GB
- 用途：Docker Compose 部署 React + Nginx + FastAPI + PostgreSQL + Redis 的演示环境

选择原因：

- 2 核 4G 比 2 核 2G 更稳，适合同时跑后端、前端静态服务、PostgreSQL、Redis 和构建过程。
- 本项目调用 DeepSeek API，不需要 GPU 服务器。
- 轻量应用服务器足够支撑 MVP 演示，不需要一开始上 Kubernetes、负载均衡或复杂 VPC。
- 先开 22 和 80 端口即可；443 等有域名和证书后再补。

## 登录与密码经验

本次遇到 SSH/SCP 密码登录失败，最终确认：

- 服务器内当前用户是 `ubuntu`，可通过 `whoami` 确认。
- Ubuntu 上需要确认 SSH 允许密码登录：

```bash
printf 'PasswordAuthentication yes\nKbdInteractiveAuthentication yes\nUsePAM yes\n' | sudo tee /etc/ssh/sshd_config.d/99-password-auth.conf
sudo sshd -t
sudo systemctl restart ssh
```

- 如果购买服务器时的密码无法用于 `ubuntu` 用户，可在服务器终端重设：

```bash
sudo passwd ubuntu
```

- Windows PowerShell 管理员窗口和普通窗口可能表现不同。本次普通 PowerShell 中：

```powershell
ssh ubuntu@43.136.25.67 "echo ssh-login-ok"
```

成功返回 `ssh-login-ok`。

经验：

- 不要把服务器密码或 API Key 发到聊天里。
- 密码只输入 SSH、SCP、服务器 `.env.production` 或云厂商控制台。
- 如果未来可控，建议改为 SSH Key 登录，减少重复输密码和 SCP 交互失败。

## Docker 部署经验

服务器已完成：

- Docker 安装。
- Docker Compose 可用。
- Docker registry mirror 已配置。
- `sudo docker run hello-world` 成功。

部署使用本地 PowerShell 脚本：

```powershell
cd G:\manufacturing-ai-agent
.\scripts\upload_and_deploy_cloud.ps1 -User ubuntu -ServerIp 43.136.25.67 -BaseUrl http://43.136.25.67
```

注意：

- 这个命令在本地 Windows PowerShell 执行，不是在服务器 SSH 里执行。
- 服务器里没有 `G:\manufacturing-ai-agent`，也不能运行 `.ps1` 本地脚本。
- 服务器部署目录是：

```bash
cd ~/manufacturing-ai-agent-cloud
```

服务器侧常用命令：

```bash
sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production ps
sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production logs --tail=160 backend
curl http://127.0.0.1/health
```

## 数据库与环境变量经验

本次遇到 PostgreSQL 认证失败：

```text
password authentication failed for user "agent_user"
```

原因是容器数据卷里已有旧数据库初始化密码，而 `.env.production` 中密码变化后，PostgreSQL 不会自动重置已有数据卷密码。

处理方式：

- 如果是一次性演示环境，可通过部署脚本的 `-ResetDemoVolume` 清理旧演示数据卷。
- 如果不是一次性环境，不能随便删 volume，应进入数据库调整密码或迁移数据。

经验：

- `.env.production` 只放服务器，不进云包、不进 Git、不写文档明文。
- `POSTGRES_PASSWORD`、`DATABASE_URL`、`AUTH_SECRET_KEY` 必须同步。
- 生产或演示服务器上不要使用默认 demo secret。

## DeepSeek API 经验

本项目使用 DeepSeek API，不需要本地 GPU。

配置只放服务器 `.env.production`：

```env
LLM_GATEWAY_MODE=deepseek
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=<只在服务器输入>
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_TIMEOUT_SECONDS=20
```

测试 DeepSeek Key 是否可用：

```bash
set -a
source .env.production
set +a

curl -sS -w "\nHTTP_STATUS=%{http_code}\n" \
  -H "Authorization: Bearer ${DEEPSEEK_API_KEY}" \
  "${DEEPSEEK_BASE_URL:-https://api.deepseek.com}/models"
```

本次曾返回：

```text
Authentication Fails ... api key ... is invalid
HTTP_STATUS=401
```

经验：

- `401` 基本就是 Key 无效、复制错误、已撤销或账号权限问题。
- 如果 API Key 曾经粘贴进聊天，应按泄露处理，去 DeepSeek 控制台作废并新建。
- DeepSeek 调用失败时，当前项目可以 fallback，但业务结论仍以只读工具和模拟数据为主。

## 部署验证经验

云端验证通过命令：

```bash
python3 scripts/verify_cloud_deployment.py --base-url http://43.136.25.67 --environment cloud
```

验证覆盖：

- `GET /health`
- React 前端页面
- `POST /api/auth/login`
- `POST /api/chat`
- `GET /api/admin/usage-stats`
- `GET /api/admin/metrics`

本次云端已验证：

- Nginx 能访问前端。
- `/health` 正常。
- 登录正常。
- `/api/chat` 能跑通订单发货风险分析。
- 管理员看板接口能返回 usage 和 metrics。
- `docs/cloud-deployment-check-report.md` 已被拉回本地并显示 `Status: Verified`。

经验：

- 验证脚本通过不代表 UI 体验完整，只代表主链路和接口可用。
- 部署后浏览器可能缓存旧前端，需要 `Ctrl+F5` 强制刷新。
- 后续 UI 体验问题应作为产品化阶段继续优化，不要误判成部署失败。

## 本次主要踩坑

- SCP 反复要求密码，原因与 SSH 密码登录配置、`ubuntu` 用户密码、PowerShell 环境有关。
- 在服务器 SSH 中误执行 Windows 路径和 PowerShell 脚本，正确做法是在本地 PowerShell 执行上传脚本。
- Docker build 下载依赖时看似“卡住”，实际是在低速下载 wheel，可以等待或观察网络。
- PostgreSQL 旧 volume 会保留旧密码，`.env.production` 改密码不会自动改变已有数据库用户密码。
- DeepSeek Key 需要单独测试，不能因为项目主链路通过就认为 API Key 一定可用。
- 验证脚本通过后，仍可能出现前端请求体、中文展示、权限 UI 等体验问题，需要继续产品化。

## 后续增量追加区

后续只在这里追加新增经验，不覆盖上面的首次部署记录。

- 待追加：HTTPS / 域名 / 证书配置经验。
- 待追加：SSH Key 登录替代密码登录经验。
- 待追加：云端日志只读 API 和部署中心页面完善经验。
