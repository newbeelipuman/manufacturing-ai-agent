# Cloud Deployment Check Report

Status: Verified

Date: 2026-06-25T03:34:55.103393+00:00

Server:

- Provider:
- Region:
- Public IP: http://43.136.25.67
- OS:
- CPU / Memory:

Note: Fill provider, region, public IP, OS, and CPU / memory after a real cloud run.

## Boundary

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。

## Verification Checklist

- [x] Security group opened for SSH and HTTP.
- [x] Docker Engine installed.
- [x] Repository uploaded or cloned.
- [x] `.env.production` created from `.env.production.example`.
- [x] Default `POSTGRES_PASSWORD` changed.
- [x] Default `AUTH_SECRET_KEY` changed.
- [x] `python scripts/check_production_env.py --env-file .env.production` passed.
- [x] `docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production config` passed.
- [x] `docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production up -d --build` passed.
- [x] `python -m app.db.init_db` ran in backend container.
- [x] `python scripts/seed_demo_data.py` ran in backend container.
- [x] `curl http://43.136.25.67/health` returned healthy response.
- [x] React console opened through Nginx.
- [x] `demo_admin / demo123456` login worked.
- [x] Chat workbench called `/api/chat` successfully.
- [x] Admin dashboard loaded usage stats and metrics.
- [x] `python scripts/verify_cloud_deployment.py --base-url http://43.136.25.67` passed.

## Command Evidence

```bash
python scripts/verify_cloud_deployment.py --base-url http://43.136.25.67
```

```json
{
  "base_url": "http://43.136.25.67",
  "checked_at": "2026-06-25T03:34:55.103393+00:00",
  "boundary": "MVP prototype with simulated ERP/MES/WMS data; Agent business tools remain read-only and do not execute outbound, adjustment, approval, purchase, order, or work-order write actions.",
  "checks": {
    "health": {
      "status_code": 200,
      "success": true,
      "body": {
        "status": "ok",
        "app": "manufacturing-ai-agent",
        "version": "0.1.0",
        "environment": "production"
      }
    },
    "frontend": {
      "status_code": 200,
      "success": true,
      "title_found": true,
      "root_div_found": true
    },
    "login": {
      "status_code": 200,
      "success": true,
      "user": {
        "username": "demo_admin",
        "display_name": "管理员",
        "role": "admin"
      }
    },
    "chat": {
      "status_code": 200,
      "success": true,
      "called_tools": [
        "query_order_status",
        "query_inventory_by_sku",
        "query_purchase_arrival",
        "query_exception_sop"
      ],
      "risk_level": "high"
    },
    "admin_dashboard": {
      "success": true,
      "usage_stats": {
        "status_code": 200,
        "keys": [
          "agent_calls_by_role",
          "avg_latency_ms",
          "date_from",
          "date_to",
          "denied_rate",
          "intent_distribution",
          "permission_denied_by_role",
          "permission_denied_count",
          "risk_level_distribution",
          "success",
          "success_rate",
          "tool_calls_by_name",
          "top_intents",
          "top_tools",
          "total_agent_calls",
          "total_estimated_tokens",
          "total_tool_calls",
          "total_usage_requests"
        ]
      },
      "metrics": {
        "status_code": 200,
        "keys": [
          "avg_latency_ms",
          "denied_rate",
          "high_risk_count",
          "success",
          "success_rate",
          "total_agent_calls",
          "total_requests",
          "total_tool_calls"
        ]
      }
    }
  },
  "success": true
}
```

## Result

Verified.

This report is evidence for the environment named above. Do not describe it as production deployment or real enterprise rollout.
