# Agent Orchestration

当前项目是 MVP，Agent 编排先用规则和正则实现，不引入 LLM。

目标链路：

```text
intent -> entity -> plan -> permission -> tools -> answer -> audit
```

## 当前实现

- intent：`app/services/agent_service.py` 通过关键词和编号规则识别订单发货、工单齐套、采购延期、库存批次和 SOP 异常问题。
- entity：当前先抽取订单号、工单号、采购单号和 SKU；缺少必要实体时返回澄清问题，不默认查询 `O1001`。
- plan：P0.5 仍保留当前分支路由，响应中补充 `execution_trace`。
- permission：工具执行仍统一走 `execute_tool()`，确保允许和拒绝都写入 `tool_call_log`。
- tools：所有业务工具保持只读，只查询或分析模拟 ERP/MES/WMS 数据和 SOP 文档。
- answer：回答需要说明检查了什么数据、调用了哪些工具、权限是否允许、业务结论、建议下一步和人工确认提醒。
- audit：`agent_call_log` 记录问题和答案摘要，`tool_call_log` 记录每次工具调用或拒绝。
- shipment risk：订单发货风险由 `shipment_risk_service.py` 计算，输出 `can_ship`、`partial_ship`、`shortage_risk`、`delivery_delay_risk`、`manual_review_required`、`evidence` 和 `recommendations`。

## 后续重构方向

P1 将把 `agent_service.chat()` 拆成更清晰的服务：

- `intent_service.py`
- `entity_extractor.py`
- `tool_planner.py`
- `permission_guard.py`
- `execution_trace.py`
- `answer_composer.py`

拆分后，`agent_service.chat()` 只负责串联编排流程。
