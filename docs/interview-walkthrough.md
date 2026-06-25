# Interview Walkthrough

## 3 分钟项目介绍

这是一个制造业企业内部 AI Agent 全栈 MVP。它不接真实 ERP/MES/WMS，也不执行写侧业务动作，而是用模拟 ERP/MES/WMS 数据演示 React 管理台、自然语言业务查询、只读工具调用、SOP 检索、JWT/RBAC、权限申请审批、审计日志、用量统计、Docker/Nginx 本地全栈部署和 CI/观测性。

核心演示问题有 5 个：

```text
订单 O1001 现在能不能发货？
工单 WO1001 今天能不能开工，缺哪些物料？
采购单 PO1001 延期会影响哪些客户订单？
SKU-KB-001 当前可用库存是多少？有哪些批次？
注塑件外观不良应该怎么处理？
```

每个回答都会说明检查了什么数据、调用了哪些工具、权限是否允许、业务结论、建议下一步，并提醒高风险业务动作需要人工确认。

## 为什么不是普通 RAG

普通 RAG 通常只做“问题 -> 检索 -> 生成回答”。本项目的重点是制造业业务查询链路：

- 先识别业务意图和实体，例如订单号、工单号、采购单号、SKU。
- 根据意图规划只读工具调用。
- 每次工具调用前做角色权限校验。
- 权限允许时查询模拟业务表或 SOP 知识库。
- 权限拒绝时不查业务数据，但仍写入 `tool_call_log`。
- 最后返回可解释的 `execution_trace`、`risk_level`、`evidence` 和 `recommendations`。

SOP 检索只是其中一类工具。订单、库存、工单、采购延期这些问题会组合多个只读工具，并经过权限与审计链路。

## 一次 `/api/chat` 请求链路

以“订单 O1001 现在能不能发货？”为例：

1. `routes_chat.py` 接收请求，调用 `agent_service.chat()`。
2. `entity_extractor.py` 抽取 `order_no=O1001`。
3. `intent_service.py` 判断意图为 `order_delivery_risk`。
4. `tool_planner.py` 生成分析路径和只读工具计划。
5. `permission_guard.py` 对计划做预检查，用于 trace 展示。
6. `analysis_service.py` 编排复合分析。
7. `tool_service.py` 在每个工具执行前调用权限检查，并写入 `tool_call_log`。
8. `business_tools.py` 查询模拟订单、库存、采购和 SOP 数据。
9. `answer_composer.py` 组合业务回答。
10. `audit_service.py` 写入 `agent_call_log`，保存响应 JSON 和 trace。
11. `usage_service.py` 记录用量统计。

如果请求来自 React 控制台，前端先通过 `/api/auth/login` 获取 JWT。后端会在 token 与 body/query role 同时存在时优先使用 token 身份，避免前端伪造角色。

## 权限、审计、只读边界、字段过滤

权限：

- `admin` 可以查看管理日志和用量统计。
- `sales`、`warehouse`、`purchase`、`production_manager` 只能访问各自授权的业务查询。
- `normal_user` 只能查询公开 SOP 或通用知识，不能查询订单、库存、工单、采购业务数据。

审计：

- 每次 `/api/chat` 会写入 `agent_call_log`。
- 每次工具调用会写入 `tool_call_log`。
- 权限拒绝也必须写入 `tool_call_log`，用于展示越权尝试。

只读边界：

- 工具名只使用 `query_`、`search_`、`get_`、`analyze_` 等只读前缀。
- 工具只返回查询或分析建议，不执行出库、调账、审批、下单、写入业务系统等动作。

字段过滤：

- `response_filter.py` 根据角色过滤敏感字段。
- 普通用户和部分业务角色不会看到成本、采购价格、客户敏感信息等字段。

平台权限申请：

- 普通用户可以申请平台权限，例如查看某个菜单。
- Admin 在 Approval Center 审批通过后，系统写入 `auth_user_permission_grant`。
- 申请和审批写入 `tool_call_log`，但这不是订单、采购、出库等业务审批。

观测性：

- request id middleware 为每次请求生成或透传 `x-request-id`。
- `agent_call_log` 和 `tool_call_log` 写入同一个 request id，便于串联排查。
- `/api/admin/metrics` 汇总请求量、调用量、成功率、拒绝率、平均延迟和高风险数量。

## 当前限制

- 当前是 MVP，不是生产系统。
- 当前不接真实 LLM，意图识别和实体抽取主要使用规则与正则。
- 当前数据来自模拟 ERP/MES/WMS 表和本地 SOP 文档。
- 当前 SOP 检索是轻量关键词检索，不是外部向量库。
- 当前已有 React 控制台，但仍是 MVP demo，不是生产系统。
- 当前云服务器部署只有购买指南、runbook 和 check report 模板；未伪造真实云部署结果。

## 真实企业接入路径

后续接入真实企业系统时，可以保持 Agent 编排、权限、审计和响应结构不变，把模拟数据查询层替换为：

- ERP/MES/WMS 的只读 API。
- 只读数据库视图。
- 企业数据中间表。
- 本地或私有化知识库索引。

即使接入真实系统，Agent 仍应保持只读查询和分析边界。出库、调账、审批、下单、客户承诺等高风险业务动作必须由业务人员在企业系统中人工确认执行。
