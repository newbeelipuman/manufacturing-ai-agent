# Cloud Server Buying Guide

## Scope

This guide prepares a cloud-server deployment verification for the MVP. It must not be described as production rollout, real customer deployment, or real ERP/MES/WMS integration.

Boundary:

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

## Recommended Instance

- CPU: 2 cores.
- Memory: 4 GB recommended.
- Disk: 40 GB SSD or larger.
- OS: Ubuntu 22.04 LTS or Ubuntu 24.04 LTS.
- Bandwidth: 3 Mbps or higher for a small demo.

Budget fallback:

- 2 cores / 2 GB can work for a short demo, but building frontend assets and running PostgreSQL, Redis, backend, and Nginx together may be tight.

## Security Group

Open only what is needed:

- `22/tcp`: SSH, restricted to your own IP when possible.
- `80/tcp`: HTTP demo entry.
- `443/tcp`: HTTPS after a domain and certificate are ready.
- `8080/tcp`: temporary debugging only; do not keep it open for a long-lived demo.

## Before Purchase

Complete local fullstack verification first:

```bash
cd frontend
npm run build
cd ..
docker compose config
```

Do not buy the server before local Docker/Nginx integration is healthy.

## Resume-Safe Wording

Allowed:

```text
使用云服务器完成 Docker Compose 部署验证，Nginx 托管 React 前端并反代 FastAPI API，PostgreSQL 持久化模拟业务数据，形成可复现部署文档和检查报告。
```

Not allowed:

```text
生产级上线。
真实企业部署。
真实 ERP 接入。
企业客户已使用。
```
