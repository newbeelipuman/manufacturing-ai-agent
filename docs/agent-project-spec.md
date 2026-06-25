# Manufacturing AI Agent MVP Spec

This document keeps the detailed product rules out of the root `AGENTS.md`. Coding agents should read it when implementing product behavior, data models, routes, tools, or README content.

## Project Summary

Project name: `manufacturing-ai-agent`

Chinese name: `企业 AI Agent 平台：制造业 ERP/MES/WMS 业务查询与知识库助手（MVP 原型）`

The project is a manufacturing business query Agent MVP for internal enterprise use. It is not a generic chatbot and not an isolated PDF Q&A system.

Core flow:

```text
用户自然语言提问
→ 识别用户角色
→ 权限校验
→ Agent 判断问题类型
→ 调用只读业务工具 / RAG 知识库
→ 生成业务回答
→ 记录调用审计和用量
```

The business scope covers sales orders, inventory batches, work orders, purchase arrivals, material shortages, delivery risks, production exception SOPs, warehouse rules, audit logs, and usage statistics.

## Phase Priority

### P0

Required first:

1. FastAPI base app.
2. PostgreSQL tables or a documented local fallback for early development.
3. Simulated sales order, inventory, work order, and purchase data.
4. Five read-only tools.
5. Agent routing to tools or RAG.
6. SOP RAG retrieval.
7. Permission check.
8. Audit logging.
9. Docker Compose startup.
10. README with project boundaries and demo questions.

Database direction: use PostgreSQL for the Docker/demo backend and SQLite only as a local development or pytest fallback. Do not plan MySQL for the current MVP unless project scope is explicitly changed.

### P1

Only after P0 works:

1. Redis cache or session.
2. Usage statistics.
3. Nginx reverse proxy.
4. Simple admin log APIs.
5. Unified exception handling.
6. Structured logging.
7. `.env` config cleanup.
8. OpenAPI docs cleanup.

### P2

Only after P1 works:

1. Simple React or Vue frontend.
2. Multi-model config.
3. Model routing prototype.
4. CI/CD script.
5. More complex LangGraph state flow.
6. Rerank.
7. Document upload.
8. User management UI.

## Recommended Structure

```text
manufacturing-ai-agent/
├── AGENTS.md
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── logging.py
│   │   └── permissions.py
│   ├── api/
│   │   ├── routes_chat.py
│   │   ├── routes_tools.py
│   │   ├── routes_knowledge.py
│   │   └── routes_admin.py
│   ├── models/
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── inventory.py
│   │   ├── work_order.py
│   │   ├── purchase.py
│   │   ├── knowledge.py
│   │   └── audit.py
│   ├── schemas/
│   ├── services/
│   ├── tools/
│   ├── rag/
│   └── db/
├── docs/
│   ├── sop/
│   ├── api.md
│   ├── deployment.md
│   └── interview_notes.md
├── scripts/
├── docker/
├── docker-compose.yml
├── .env.example
├── requirements.txt
└── README.md
```

Minor adjustments are acceptable when they preserve the main architecture.

## Data Model

### User and Role

Table: `user_account`

Suggested fields:

* `id`
* `username`
* `display_name`
* `role`
* `is_active`
* `created_at`
* `updated_at`

Roles:

* `admin`
* `production_manager`
* `sales`
* `warehouse`
* `purchase`
* `normal_user`

### Sales Order

Tables:

* `sales_order`
* `sales_order_item`

Suggested `sales_order` fields:

* `id`
* `order_no`
* `customer_name`
* `order_status`
* `delivery_status`
* `planned_delivery_date`
* `created_at`
* `updated_at`

Suggested `sales_order_item` fields:

* `id`
* `order_no`
* `sku_code`
* `sku_name`
* `quantity`
* `delivered_quantity`
* `locked_quantity`
* `created_at`
* `updated_at`

### Inventory

Tables:

* `inventory_sku`
* `inventory_batch`
* `inventory_transaction`

Suggested `inventory_sku` fields:

* `id`
* `sku_code`
* `sku_name`
* `total_quantity`
* `available_quantity`
* `locked_quantity`
* `unit`
* `updated_at`

Suggested `inventory_batch` fields:

* `id`
* `sku_code`
* `batch_no`
* `warehouse_code`
* `quantity`
* `available_quantity`
* `locked_quantity`
* `production_date`
* `expire_date`
* `updated_at`

Suggested `inventory_transaction` fields:

* `id`
* `sku_code`
* `batch_no`
* `transaction_type`
* `quantity`
* `source_doc_no`
* `created_at`

### Work Order

Tables:

* `work_order`
* `work_order_material`

Suggested `work_order` fields:

* `id`
* `work_order_no`
* `product_sku`
* `product_name`
* `planned_quantity`
* `finished_quantity`
* `status`
* `planned_start_date`
* `planned_end_date`
* `created_at`
* `updated_at`

Suggested `work_order_material` fields:

* `id`
* `work_order_no`
* `material_sku`
* `material_name`
* `required_quantity`
* `issued_quantity`
* `created_at`
* `updated_at`

### Purchase

Tables:

* `purchase_order`
* `purchase_order_item`

Suggested `purchase_order` fields:

* `id`
* `purchase_order_no`
* `supplier_name`
* `status`
* `expected_arrival_date`
* `is_delayed`
* `created_at`
* `updated_at`

Suggested `purchase_order_item` fields:

* `id`
* `purchase_order_no`
* `sku_code`
* `sku_name`
* `quantity`
* `arrived_quantity`
* `created_at`
* `updated_at`

### Knowledge Base

Tables:

* `knowledge_document`
* `knowledge_chunk`

Suggested `knowledge_document` fields:

* `id`
* `title`
* `doc_type`
* `source_path`
* `status`
* `created_at`
* `updated_at`

Suggested `knowledge_chunk` fields:

* `id`
* `document_id`
* `chunk_text`
* `chunk_index`
* `metadata_json`
* `created_at`

### Audit and Usage

Tables:

* `agent_call_log`
* `tool_call_log`
* `usage_stat`

Suggested `agent_call_log` fields:

* `id`
* `user_id`
* `username`
* `role`
* `question`
* `answer_summary`
* `model_name`
* `estimated_prompt_tokens`
* `estimated_completion_tokens`
* `latency_ms`
* `success`
* `error_message`
* `created_at`

Suggested `tool_call_log` fields:

* `id`
* `agent_call_id`
* `user_id`
* `role`
* `tool_name`
* `tool_args_json`
* `tool_result_summary`
* `permission_allowed`
* `success`
* `error_message`
* `latency_ms`
* `created_at`

Suggested `usage_stat` fields:

* `id`
* `user_id`
* `username`
* `role`
* `date`
* `request_count`
* `tool_call_count`
* `estimated_tokens`
* `created_at`
* `updated_at`

## Demo Data

Required identifiers:

* sales order: `O1001`
* work order: `WO1001`
* purchase order: `PO1001`
* SKU: `SKU-KB-001`
* material examples: 键帽、轴体、PCB、注塑件、包装盒
* batch: `BATCH-KB-202601`
* warehouse: `WH-DG-01`

Recommended delivery-risk scenario:

```text
订单 O1001 需要 SKU-KB-001 键帽 1000 件。
当前可用库存只有 600 件，锁定库存 200 件。
采购单 PO1001 预计补货 800 件，但状态为延期。
因此 O1001 存在发货风险。
```

Recommended work-order readiness scenario:

```text
工单 WO1001 计划生产机械键盘 500 台。
需要键帽、轴体、PCB、注塑件、包装盒。
其中键帽和注塑件不足。
系统应返回缺料清单。
```

Recommended SOP scenario:

```text
注塑件外观不良 SOP：
1. 隔离异常批次；
2. 通知质检复判；
3. 记录异常数量和批次；
4. 判断是否返工、报废或让步接收；
5. 涉及客户订单时同步销售和生产主管；
6. Agent 只提供建议，不自动执行业务动作。
```

## Permission Matrix

### `admin`

Can query orders, inventory, work orders, purchase orders, SOP content, audit logs, and usage statistics.

### `sales`

Can query orders, delivery status, inventory sufficiency, and delivery-related SOP content.

Cannot view sensitive purchase data or full audit logs.

### `warehouse`

Can query SKU inventory, inventory batches, inventory transactions, and warehouse SOP content.

Cannot adjust inventory, approve outbound operations, or view unrelated purchase-sensitive fields.

### `production_manager`

Can query work orders, shortages, inventory, production exception SOP content, and work-order readiness.

Cannot approve work orders, update work orders, or issue materials.

### `purchase`

Can query purchase orders, expected arrivals, purchase delay impact, and related material inventory.

Cannot create purchase orders, update purchase orders, approve purchases, or view unrelated order-sensitive fields.

### `normal_user`

Can query public SOP or general knowledge content.

Cannot query orders, inventory, work orders, purchase orders, or audit logs.

## Required Tools

### `query_order_status`

Reads sales order and sales order item data.

Input:

* `order_no`

Returns:

* order status
* customer
* planned delivery date
* delivery status
* order items
* SKU code
* SKU name
* ordered quantity
* delivered quantity
* locked quantity

### `query_inventory_by_sku`

Reads SKU inventory and batch data.

Input:

* `sku_code`

Returns:

* SKU name
* total quantity
* available quantity
* locked quantity
* batch list
* warehouse code
* batch quantity
* batch available quantity

### `query_work_order`

Reads work order and material requirement data.

Input:

* `work_order_no`

Returns:

* work order status
* product SKU
* planned quantity
* finished quantity
* planned start date
* material requirements
* available inventory
* shortage list

### `query_purchase_arrival`

Reads purchase order and purchase item data.

Input:

* `purchase_order_no`

Returns:

* purchase order status
* supplier
* expected arrival date
* delay status
* item list
* ordered quantity
* arrived quantity
* remaining quantity

### `query_exception_sop`

Reads SOP knowledge through RAG.

Input:

* `question`
* optional `exception_type`

Returns:

* matched SOP title
* matched document
* handling steps
* notes
* manual confirmation reminder

## Composite Analysis

P0 may compose basic tools directly inside `agent_service.py`.

Potential P1 composite tools:

* `analyze_order_delivery_risk`
* `analyze_work_order_readiness`
* `analyze_purchase_delay_impact`

Composite tools must remain read-only. They can call multiple query tools and return conclusions, but must not write business data.

## RAG Rules

Knowledge base content uses local simulated documents.

Knowledge types:

* production exception SOP
* delivery rules
* after-sales return rules
* quality inspection standards
* warehouse stocktaking rules
* permission explanation
* internal system manual

RAG must not become an isolated PDF Q&A feature. It should combine with business queries when the question requires both business data and procedural guidance.

For this question:

```text
订单 O1001 因为键帽缺料不能发货，应该怎么处理？
```

Expected flow:

```text
1. query order;
2. query order items;
3. query SKU inventory;
4. query purchase arrival;
5. retrieve shortage SOP;
6. generate business answer;
7. write audit logs.
```

RAG answers must include a manual confirmation reminder when actions involve outbound, adjustment, approval, scrap, concession, or customer delivery changes.

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

Admin APIs require `admin` role. Tool debug APIs are allowed for demo and testing, but must still respect permission checks.

## README Checklist

README must include:

* project name
* project background
* project boundaries
* tech stack
* architecture
* directory structure
* data model
* user roles
* permission rules
* Agent tools
* RAG knowledge base
* audit logging
* Docker Compose startup
* database initialization
* vector store build
* 5 demo questions
* future real enterprise integration approach
* explicit statement that write-side business operations are forbidden

README must be honest. Do not write that real ERP/MES/WMS is integrated, real production systems are online, real orders are served, production efficiency improved by a percentage, cost reduced by a percentage, or automatic inventory adjustment/outbound/approval is supported.
