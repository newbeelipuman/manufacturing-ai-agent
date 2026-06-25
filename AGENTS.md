# AGENTS.md

Coding-agent instructions for `manufacturing-ai-agent`.

This repository is a job-oriented MVP for a manufacturing enterprise AI Agent backend. It should demonstrate natural-language business querying, read-only tool calls, RAG retrieval, role permissions, audit logs, usage tracking, and Docker-based startup.

For the detailed product spec, read [docs/agent-project-spec.md](docs/agent-project-spec.md). Keep this root file as the high-signal operational guide.

## Working Order

1. Inspect the existing files before editing.
2. Prioritize the P0 demo chain until it works end to end.
3. Keep changes small and directly tied to the current P0 milestone.
4. Prefer existing project patterns once files exist.
5. Update README or docs when API behavior, startup steps, or boundaries change.

Do not spend time on frontend, multi-tenancy, Kubernetes, complex CI/CD, real ERP integration, or advanced model routing before the 5 required demo questions work.

## Useful Commands

Run only the commands that match the files currently present.

```bash
python -m venv .venv
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
python -m compileall app
pytest
docker compose config
docker compose up --build
```

For a running local API, verify at least:

```bash
curl http://localhost:8000/health
```

## Non-Negotiable Boundaries

This is an MVP prototype using simulated ERP/MES/WMS data.

Never claim that the project has real enterprise production integration. Never connect to real ERP/MES/WMS systems unless the user explicitly changes the project scope. Never implement write-side business operations.

All Agent tools must be read-only. A tool may query or analyze data and return suggestions, but it must not approve, submit, adjust, delete, dispatch, issue, update, or write business data.

Allowed tool prefixes:

* `query_`
* `search_`
* `get_`
* `analyze_`

Forbidden tool prefixes:

* `create_`
* `update_`
* `delete_`
* `approve_`
* `submit_`
* `adjust_`
* `outbound_`
* `issue_`
* `write_`

Do not write fake metrics such as efficiency improvement percentages, cost reduction percentages, production-proven claims, or real customer deployment claims.

README must include this boundary wording:

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

## P0 Scope

P0 is complete only when the backend can demonstrate:

* FastAPI base app and `GET /health`;
* PostgreSQL-backed table models or clearly documented local development fallback;
* simulated sales order, inventory, work order, purchase, knowledge, audit, and usage data;
* 5 read-only tools;
* basic Agent routing from `/api/chat`;
* SOP RAG retrieval;
* role permission checks before every tool call;
* `agent_call_log` and `tool_call_log` records, including permission denial attempts;
* Docker Compose startup;
* README with startup steps, boundaries, and demo questions.

## Required Demo Questions

The completed MVP must support these questions:

```text
订单 O1001 现在能不能发货？
工单 WO1001 今天能不能开工，缺哪些物料？
采购单 PO1001 延期会影响哪些客户订单？
SKU-KB-001 当前可用库存是多少？有哪些批次？
注塑件外观不良应该怎么处理？
```

Each answer should state what data was checked, which tools were called, whether permission allowed the call, the business conclusion, suggested next action, and a reminder that risky business actions require human confirmation.

## Architecture Rules

Prefer this ownership model:

* `app/api/`: FastAPI route handlers. Keep them thin.
* `app/services/`: orchestration, permissions, audit, usage, RAG service logic.
* `app/tools/`: read-only business query and analysis functions.
* `app/models/`: SQLAlchemy database models.
* `app/schemas/`: Pydantic request and response models.
* `app/rag/`: loader, splitter, embedding, vector store, retriever code.
* `app/db/`: database session, initialization, seed helpers.
* `docs/`: SOP docs, API notes, deployment notes, interview notes.
* `scripts/`: database seed and vector-store build scripts.
* `docker/`: Dockerfile and Nginx config.

Keep route handlers thin. Business logic belongs in services and tools. Permission checks must happen before tool execution. Audit logging is part of the product, not optional cleanup.

## Tech Choices

Use these first:

* Python
* FastAPI
* SQLAlchemy
* Pydantic
* PostgreSQL
* Redis only after the P0 flow is stable
* LangGraph or LangChain
* FAISS or Chroma
* Docker and Docker Compose
* `.env` configuration
* OpenAPI / Swagger
* structured logging

Avoid adding large frameworks or new architectural layers unless they clearly serve P0.

## Business Data Rules

Demo data must feel like manufacturing data, not abstract examples.

Required identifiers:

* sales order: `O1001`
* work order: `WO1001`
* purchase order: `PO1001`
* SKU: `SKU-KB-001`
* batch: `BATCH-KB-202601`
* warehouse: `WH-DG-01`

Use terms such as SKU, batch, work order, purchase order, sales order, available inventory, locked inventory, expected arrival, material shortage, delivery date, and exception SOP.

## Permission Rules

Roles:

* `admin`
* `production_manager`
* `sales`
* `warehouse`
* `purchase`
* `normal_user`

General behavior:

* Check role permission before every tool call.
* Return a clear error when permission is denied.
* Log permission denial to `tool_call_log`.
* Filter sensitive fields before returning data.
* Admin can view audit and usage logs.
* Normal users can only query public SOP or general knowledge content.

## Required Read-Only Tools

P0 requires at least:

* `query_order_status`
* `query_inventory_by_sku`
* `query_work_order`
* `query_purchase_arrival`
* `query_exception_sop`

P0 may compose these directly in `agent_service.py`. Add explicit composite tools such as `analyze_order_delivery_risk`, `analyze_work_order_readiness`, and `analyze_purchase_delay_impact` only after the base flow works.

## Required APIs

```http
GET /health
POST /api/chat
POST /api/tools/query-order-status
POST /api/tools/query-inventory-by-sku
POST /api/tools/query-work-order
POST /api/tools/query-purchase-arrival
POST /api/tools/query-exception-sop
POST /api/knowledge/rebuild
GET /api/knowledge/search
GET /api/admin/agent-call-logs
GET /api/admin/tool-call-logs
GET /api/admin/usage-stats
```

Admin APIs require the `admin` role. Tool debug APIs are allowed for demo and testing, but they must still respect permission checks.

## Coding Style

Use explicit, readable Python. Keep functions focused. Use Pydantic schemas for request and response models. Use SQLAlchemy models for database tables. Put config in `app/core/config.py` and read it from `.env`.

Read-only tools should have docstrings and return explicit structures. Avoid scattered hard-coded config. Avoid hiding database writes inside tool functions.

When adding behavior, add focused tests if the project has a test suite. At minimum, run `python -m compileall app` after Python changes.

## Documentation Style

This project is for job demonstration, so documentation must be factual.

Prefer:

```text
目前项目是 MVP。
后端用 FastAPI。
数据是模拟 ERP/MES/WMS 表。
Agent 只做只读查询和 RAG 检索。
权限和调用日志已放在主流程里。
真实接入时可以替换接口层。
```

Avoid:

```text
深度赋能
战略匹配
闭环价值
业界领先
生产级落地
资深 Python 后端
多年 Python 经验
```

## Completion Checklist

Before saying a task is done, check the relevant items:

* Does the app start?
* Does `/health` work?
* Do seed scripts or seed helpers exist?
* Are tools still read-only?
* Does permission check run before tool execution?
* Are tool calls and denied attempts logged?
* Did API changes update README or docs?
* If Docker files changed, does `docker compose config` pass?

Do not silently introduce large architecture changes. Do not replace the manufacturing ERP/MES/WMS direction with a generic chatbot or generic RAG demo.
