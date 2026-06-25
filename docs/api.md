## Current Limits

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

`/api/chat` 当前仍是规则路由；SOP 检索是关键词匹配；所有业务数据均为模拟数据。

`/api/chat` 响应包含编排字段：`intent`、`entities`、`execution_trace`、`risk_level`、`evidence`、`recommendations`。订单发货风险仅做只读判断，不会执行出库、锁库、调账或审批。

# API Notes

## Health

```bash
curl http://localhost:8000/health
```

## Chat

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_admin\",\"role\":\"admin\",\"question\":\"工单 WO1001 今天能不能开工，缺哪些物料？\"}"
```

## Tool Debug APIs

```bash
curl -X POST http://localhost:8000/api/tools/query-order-status \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_sales\",\"role\":\"sales\",\"order_no\":\"O1001\"}"

curl -X POST http://localhost:8000/api/tools/query-inventory-by-sku \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_warehouse\",\"role\":\"warehouse\",\"sku_code\":\"SKU-KB-001\"}"

curl -X POST http://localhost:8000/api/tools/query-work-order \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_pm\",\"role\":\"production_manager\",\"work_order_no\":\"WO1001\"}"

curl -X POST http://localhost:8000/api/tools/query-purchase-arrival \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_purchase\",\"role\":\"purchase\",\"purchase_order_no\":\"PO1001\"}"

curl -X POST http://localhost:8000/api/tools/query-exception-sop \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_user\",\"role\":\"normal_user\",\"question\":\"注塑件外观不良应该怎么处理？\"}"
```

## Composite Analysis Debug APIs

```bash
curl -X POST http://localhost:8000/api/tools/analyze-order-delivery-risk \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_admin\",\"role\":\"admin\",\"order_no\":\"O1001\"}"

curl -X POST http://localhost:8000/api/tools/analyze-work-order-readiness \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_pm\",\"role\":\"production_manager\",\"work_order_no\":\"WO1001\"}"

curl -X POST http://localhost:8000/api/tools/analyze-purchase-delay-impact \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"demo_purchase\",\"role\":\"purchase\",\"purchase_order_no\":\"PO1001\"}"
```

复合分析接口仍保持只读。入口会检查 `analyze_*` 权限，底层订单、库存、工单、采购和 SOP 工具也会分别检查权限并写入 `tool_call_log`。

## Knowledge

```bash
curl -X POST "http://localhost:8000/api/knowledge/rebuild?role=admin"
curl "http://localhost:8000/api/knowledge/search?query=注塑件外观不良&role=normal_user"
```

## Admin Logs

```bash
curl "http://localhost:8000/api/admin/agent-call-logs?role=admin"
curl "http://localhost:8000/api/admin/tool-call-logs?role=admin"
curl "http://localhost:8000/api/admin/tool-call-logs/1?role=admin"
curl "http://localhost:8000/api/admin/usage-stats?role=admin"
```

Audit list filters are optional:

- `GET /api/admin/agent-call-logs`: `request_id`, `username`, `log_role`, `intent`, `risk_level`, `success`, `limit`.
- `GET /api/admin/tool-call-logs`: `request_id`, `username`, `log_role`, `tool_name`, `permission_allowed`, `success`, `limit`.

非 admin 角色访问管理接口会返回 403。

示例错误响应：

```json
{
  "success": false,
  "error": {
    "code": 403,
    "message": "仅 admin 角色可以访问管理接口。"
  }
}
```

## PostgreSQL Docker 初始化

```bash
cp .env.example .env
docker compose config
docker compose up --build
docker compose exec backend python -m app.db.init_db
docker compose exec backend python scripts/seed_demo_data.py
```

Nginx 入口：

```bash
curl http://localhost:8080/health
open http://localhost:8080/docs
```

## Test Commands

```bash
python -m compileall app
pytest
docker compose config
```

## Platform Permission Audit

These APIs manage platform RBAC data only. They do not approve orders, purchases,
stock movements, work orders, outbound delivery, or any ERP/MES/WMS business write.

```bash
curl "http://localhost:8000/api/admin/permission-change-logs" \
  -H "Authorization: Bearer <admin-token>"

curl "http://localhost:8000/api/admin/role-permissions/sales" \
  -H "Authorization: Bearer <admin-token>"

curl -X POST "http://localhost:8000/api/admin/role-permissions/sales" \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d "{\"permission_codes\":[\"menu:chat\"],\"remark\":\"管理员更改权限，原因已确认。\"}"
```

Permission decisions require `approval_comment`. Approved/rejected requests write
`permission_change_log` with `source=request_approval`. Direct admin role permission
saves require `remark` and write `source=admin_direct_change`.

`GET /api/admin/permission-change-logs` supports optional filters:
`source`, `operator_username`, `target_type`, `target_identifier`,
`permission_code`, `request_id`, and `limit`.

## Deployment Center Read-Only APIs

These APIs are admin-only and read operational status/log text. They do not start,
stop, restart, rebuild, deploy, or modify containers.

```bash
curl "http://localhost:8000/api/admin/deployment/status" \
  -H "Authorization: Bearer <admin-token>"

curl "http://localhost:8000/api/admin/deployment/logs/backend?tail=120" \
  -H "Authorization: Bearer <admin-token>"
```

Allowed log services are `backend`, `nginx`, `postgres`, and `redis`. If Docker is
not readable from the current runtime, the API returns a fallback message and the
read-only command that an admin can run on the server.
