# Deployment Check Report

Generated at: 2026-06-24 13:30 Asia/Shanghai

本报告记录当前本机 Docker 演示环境验证结果。未伪造云服务器或真实企业部署结果。

## 边界

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

## 已执行命令

| command | result |
| --- | --- |
| `python -m compileall app` | passed |
| `pytest` | passed, 33 tests |
| `python scripts/run_rag_eval.py` | passed, generated `docs/rag-eval-report.md` |
| `python scripts/run_demo_report.py` | passed, generated `docs/demo-report.md` |
| `docker compose config` | passed |
| `docker compose up -d --build` | passed |
| `docker compose exec backend python -m app.db.init_db` | passed |
| `docker compose exec backend python scripts/seed_demo_data.py` | passed |
| `curl http://localhost:8080/health` | passed |
| `Invoke-RestMethod http://localhost:8080/api/chat` | passed |

## Docker 状态

`docker compose ps` 显示：

- `manufacturing-ai-agent-backend-1`: up, port `8000`
- `manufacturing-ai-agent-nginx-1`: up, port `8080`
- `manufacturing-ai-agent-postgres-1`: up, healthy, port `5432`
- `manufacturing-ai-agent-redis-1`: up, port `6379`

## Health Check

`curl http://localhost:8080/health` 返回：

```json
{"status":"ok","app":"manufacturing-ai-agent","version":"0.1.0","environment":"docker"}
```

## Chat Check

通过 Nginx 入口请求：

```powershell
$body = @{username='demo_sales'; role='sales'; question='订单 O1001 现在能不能发货？'} | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri http://localhost:8080/api/chat -ContentType 'application/json; charset=utf-8' -Body $body
```

结果：

- `success=true`
- `intent=order_delivery_risk`
- `called_tools` 包含 `query_order_status`、`query_inventory_by_sku`、`query_purchase_arrival`、`query_exception_sop`
- `requires_human_review=true`
- `manual_review_reason` 包含 `inventory_shortage`、`quality_hold`、`purchase_delay`
- `decision_record.llm_route.model=mock-enterprise-agent`

说明：PowerShell/curl 直接传中文 JSON 时出现过命令行引号解析问题，服务返回 422；改用 `Invoke-RestMethod` 后请求成功。终端中文显示存在编码噪声，不影响 JSON 字段和接口验证结果。

## 后续待执行

如果部署到真实 Ubuntu 22.04 私有云服务器，应重新执行 `docs/deployment-private-cloud.md` 中的命令，并记录服务器 IP、Docker 版本、Compose 版本和 `/health` 验证结果。当前未声明任何真实企业生产部署。
