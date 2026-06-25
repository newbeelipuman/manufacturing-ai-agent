# 私有化部署说明

本文档面向 Ubuntu 22.04 内网或私有云服务器演示部署。当前项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统；Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。

## 1. 服务器准备

- 建议 Ubuntu 22.04 LTS。
- 准备普通部署用户，并加入 `docker` 组。
- 确认开放内网访问端口：`8000` 后端直连端口、`8080` Nginx 演示入口。
- 不在服务器上保存真实 ERP/MES/WMS 账号或生产数据库连接。

## 2. Docker / Compose 检查

```bash
docker --version
docker compose version
docker info
```

如命令不存在，按 Docker 官方 Ubuntu 安装方式安装 Docker Engine 和 Compose 插件。

## 3. 获取代码

```bash
git clone <repo-url> manufacturing-ai-agent
cd manufacturing-ai-agent
```

## 4. 配置 `.env`

```bash
cp .env.production.example .env
```

必须修改：

- `POSTGRES_PASSWORD`
- `DATABASE_URL` 中的数据库密码

不要提交真实 `.env`。当前模板仍指向模拟数据和 mock LLM Gateway。

## 5. 校验 Compose

```bash
docker compose config
```

该命令只校验配置展开结果，不启动容器。

## 6. 启动服务

```bash
docker compose up -d --build
```

查看容器：

```bash
docker compose ps
```

## 7. PostgreSQL 初始化

```bash
docker compose exec backend python -m app.db.init_db
```

## 8. Seed Demo 数据

```bash
docker compose exec backend python scripts/seed_demo_data.py
```

这一步只写入模拟 ERP/MES/WMS 演示数据。

## 9. Nginx 反代入口

Compose 中的 Nginx 演示入口默认监听 `8080`，转发到 backend `8000`。配置见 `docker/nginx.conf`。

## 10. `/health` 验证

```bash
curl http://localhost:8080/health
```

期望返回：

```json
{"status":"ok"}
```

## 11. `/api/chat` 验证

```bash
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"username":"demo_sales","role":"sales","question":"订单 O1001 现在能不能发货？"}'
```

响应应包含 `called_tools`、`decision_record`、`requires_human_review`、`manual_review_reason`。

## 12. 日志排查

```bash
docker compose logs backend
docker compose logs nginx
docker compose logs postgres
```

常见问题：

- 数据库密码未同步：检查 `.env` 中 `POSTGRES_PASSWORD` 与 `DATABASE_URL`。
- 表不存在：执行 `docker compose exec backend python -m app.db.init_db`。
- 演示数据为空：执行 `docker compose exec backend python scripts/seed_demo_data.py`。
- 8080 不通：检查 `docker compose ps` 和 Nginx 日志。
- 权限被拒绝：确认请求 role 是否具备相应只读工具权限，`normal_user` 只能查询公开 SOP。
