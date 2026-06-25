# Demo Report

Generated at: 2026-06-25 08:47:14

本报告由 `python scripts/run_demo_report.py` 生成。脚本会先重置并 seed 模拟 ERP/MES/WMS 数据，然后通过 FastAPI TestClient 调用 `/api/chat`。

覆盖范围：5 个必答问题、admin/sales/warehouse/purchase/production_manager/normal_user 代表角色、允许与拒绝的权限路径、审计日志 call id。

## 1. 订单发货风险，销售可查询

- question: 订单 O1001 现在能不能发货？
- role: `sales`
- http_status: `200`
- success: `True`
- intent: `order_delivery_risk`
- entities: `{"order_no": "O1001"}`
- called_tools: `query_order_status, query_inventory_by_sku, query_purchase_arrival, query_exception_sop`
- permission: `query_order_status=allowed, query_inventory_by_sku=allowed, query_purchase_arrival=allowed, query_exception_sop=allowed`
- risk_level: `high`
- business_conclusion: 订单 O1001 暂不建议自动发货，库存不足或需复核，can_ship=False, partial_ship=True, shortage_risk=high, delivery_delay_risk=high. 采购单 PO1001 状态 delayed，预计到货 2026-06-28。
- agent_call_id: `1`

answer:

```text
路由意图: 订单发货风险分析 (order_delivery_risk)
分析路径: identify_order -> query_order_status -> query_inventory -> query_purchase_arrival -> query_exception_sop -> compose_answer
检查数据: 销售订单 | 销售订单明细 | SKU 库存 | 采购到货 | 交期异常 SOP
调用工具: query_order_status(allowed) | query_inventory_by_sku(allowed) | query_purchase_arrival(allowed) | query_exception_sop(allowed)
业务结论: 订单 O1001 暂不建议自动发货，库存不足或需复核，can_ship=False, partial_ship=True, shortage_risk=high, delivery_delay_risk=high. 采购单 PO1001 状态 delayed，预计到货 2026-06-28。
建议下一步: Do not complete shipment automatically; review shortage: SKU-KB-001 shortage 40. Quality owner should review held inventory before shipment commitment. Purchase should confirm delayed arrival and sales should communicate delivery risk. Production should confirm work order replenishment timing before promise date. SOP 建议参考：# 订单库存不足与交期异常处理 SOP

适用范围：销售订单因可用库存不足、锁定库存不足、采购到货延期或批次异常导致暂不建议发货时的处理。

## 处理步骤

1. 销售确认客户订单号、SKU、需求数量、计划交付日期和客户优先级。
2. 仓库复核 SKU 可用库存、锁定库存、批次状态、仓库编码和是否存在质量冻结批次。
3. 采购确认相关采购单预计到货日期、延
人工确认: Risky business actions require human confirmation in the enterprise system.
```

## 2. 工单开工齐套，生产主管可查询

- question: 工单 WO1001 今天能不能开工，缺哪些物料？
- role: `production_manager`
- http_status: `200`
- success: `True`
- intent: `work_order_readiness`
- entities: `{"work_order_no": "WO1001"}`
- called_tools: `query_work_order, query_inventory_by_sku, query_inventory_by_sku, query_exception_sop`
- permission: `query_work_order=allowed, query_inventory_by_sku=allowed, query_inventory_by_sku=allowed, query_exception_sop=allowed`
- risk_level: `high`
- business_conclusion: 工单 WO1001 暂不建议开工，存在缺料：MAT-ABS-001 缺口 40。
- agent_call_id: `2`

answer:

```text
路由意图: 工单开工齐套分析 (work_order_readiness)
分析路径: identify_work_order -> query_work_order -> query_material_inventory -> query_exception_sop -> compose_answer
检查数据: 工单 | 工单用料 | 物料库存 | 工单缺料处理 SOP
调用工具: query_work_order(allowed) | query_inventory_by_sku(allowed) | query_inventory_by_sku(allowed) | query_exception_sop(allowed)
业务结论: 工单 WO1001 暂不建议开工，存在缺料：MAT-ABS-001 缺口 40。
建议下一步: 建议生产主管确认齐套缺口，采购跟进到货，必要时调整排产。 SOP 建议参考：# 工单缺料与齐套处理 SOP

适用范围：工单开工前发现物料库存不足、齐套不完整、领料不足或采购到货不确定时的处理。

## 处理步骤

1. 生产主管确认工单号、成品 SKU、计划数量、计划开工日期和工单状态。
2. 仓库逐项复核 BOM 物料的可用库存、锁定库存、批次和仓库位置。
3. 对存在缺口的物料，采购确认在途采购单、预计到货日期和可替代供应方案
人工确认: Risky business actions require human confirmation in the enterprise system.
```

## 3. 采购延期影响，采购可查询

- question: 采购单 PO1001 延期会影响哪些客户订单？
- role: `purchase`
- http_status: `200`
- success: `True`
- intent: `purchase_delay_impact`
- entities: `{"purchase_order_no": "PO1001"}`
- called_tools: `query_purchase_arrival, query_order_status, query_exception_sop`
- permission: `query_purchase_arrival=allowed, query_order_status=allowed, query_exception_sop=allowed`
- risk_level: `high`
- business_conclusion: 采购单 PO1001 已延期，预计到货 2026-06-28，可能影响客户订单：O1001。
- agent_call_id: `3`

answer:

```text
路由意图: 采购延期影响分析 (purchase_delay_impact)
分析路径: identify_purchase_order -> query_purchase_arrival -> query_affected_orders -> query_exception_sop -> compose_answer
检查数据: 采购单 | 采购明细 | 相关销售订单 | 采购延期沟通 SOP
调用工具: query_purchase_arrival(allowed) | query_order_status(allowed) | query_exception_sop(allowed)
业务结论: 采购单 PO1001 已延期，预计到货 2026-06-28，可能影响客户订单：O1001。
建议下一步: 建议采购确认新的到货承诺，销售评估客户交期沟通，生产主管同步排产影响。 SOP 建议参考：# 采购延期沟通 SOP

适用范围：采购单延期、预计到货日期变化、供应商无法按期交付，并可能影响销售订单或工单齐套时的沟通处理。

## 处理步骤

1. 采购确认采购单号、供应商、SKU、未到数量、原预计到货日期和新的预计到货日期。
2. 采购记录延期原因，并判断是否存在替代供应、分批到货或加急运输方案。
3. 销售根据受影响 SKU 复核相关客户订单、
人工确认: Risky business actions require human confirmation in the enterprise system.
```

## 4. 库存批次，仓库可查询

- question: SKU-KB-001 当前可用库存是多少？有哪些批次？
- role: `warehouse`
- http_status: `200`
- success: `True`
- intent: `inventory_batches`
- entities: `{"sku_code": "SKU-KB-001"}`
- called_tools: `query_inventory_by_sku`
- permission: `query_inventory_by_sku=allowed`
- risk_level: `low`
- business_conclusion: SKU SKU-KB-001 available inventory is 100 pcs; batches: BATCH-KB-202601@WH-DG-01 available 100.
- agent_call_id: `4`

answer:

```text
路由意图: 库存批次查询 (inventory_batches)
分析路径: identify_sku -> query_inventory_batches -> compose_answer
检查数据: SKU inventory | inventory batches | warehouse stock
调用工具: query_inventory_by_sku(allowed)
业务结论: SKU SKU-KB-001 available inventory is 100 pcs; batches: BATCH-KB-202601@WH-DG-01 available 100.
建议下一步: Warehouse should review batch status and locked quantity before any shipment action.
人工确认: Risky business actions require human confirmation in the enterprise system.
```

## 5. 异常 SOP，普通用户可查询公开知识

- question: 注塑件外观不良应该怎么处理？
- role: `normal_user`
- http_status: `200`
- success: `True`
- intent: `exception_sop`
- entities: `{}`
- called_tools: `query_exception_sop`
- permission: `query_exception_sop=allowed`
- risk_level: `medium`
- business_conclusion: Matched exception SOP content. Reference snippet: # 注塑件外观不良 SOP

适用范围：注塑件出现划伤、黑点、色差、毛边、缩水、油污、变形等外观异常时的现场处理。

## 处理步骤

1. 隔离异常批次，暂停将该批次流入下一工序或客户订单。
2. 通知质检进行复判，记录不良现象、不良数量、批次、SKU、仓库和关联工单。
3. 生产主管确认是否存在模具、参数、原料或操作异常。
4. 质检根据标准判定返工、报
- agent_call_id: `5`

answer:

```text
路由意图: 制造异常 SOP 检索 (exception_sop)
分析路径: identify_exception_question -> query_exception_sop -> compose_answer
检查数据: SOP knowledge chunks
调用工具: query_exception_sop(allowed)
业务结论: Matched exception SOP content. Reference snippet: # 注塑件外观不良 SOP

适用范围：注塑件出现划伤、黑点、色差、毛边、缩水、油污、变形等外观异常时的现场处理。

## 处理步骤

1. 隔离异常批次，暂停将该批次流入下一工序或客户订单。
2. 通知质检进行复判，记录不良现象、不良数量、批次、SKU、仓库和关联工单。
3. 生产主管确认是否存在模具、参数、原料或操作异常。
4. 质检根据标准判定返工、报
建议下一步: Follow SOP steps and ask quality/production owners to confirm risky actions.
人工确认: Risky business actions require human confirmation in the enterprise system.
```

## 6. 订单发货风险，普通用户被拒绝

- question: 订单 O1001 现在能不能发货？
- role: `normal_user`
- http_status: `200`
- success: `False`
- intent: `order_delivery_risk`
- entities: `{"order_no": "O1001"}`
- called_tools: `analyze_order_delivery_risk`
- permission: `analyze_order_delivery_risk=denied`
- risk_level: `blocked`
- business_conclusion: 角色 normal_user 无权调用复合分析 analyze_order_delivery_risk。
- agent_call_id: `6`

answer:

```text
路由意图: 订单发货风险分析 (order_delivery_risk)
分析路径: identify_order -> query_order_status -> query_inventory -> query_purchase_arrival -> query_exception_sop -> compose_answer
检查数据: 销售订单 | 销售订单明细 | SKU 库存 | 采购到货 | 交期异常 SOP
调用工具: analyze_order_delivery_risk(denied)
业务结论: 角色 normal_user 无权调用复合分析 analyze_order_delivery_risk。
建议下一步: 请切换到有权限的业务角色，或仅查询公开 SOP 内容。
人工确认: Risky business actions require human confirmation in the enterprise system.
```

## 7. 管理员查看完整链路

- question: 订单 O1001 现在能不能发货？
- role: `admin`
- http_status: `200`
- success: `True`
- intent: `order_delivery_risk`
- entities: `{"order_no": "O1001"}`
- called_tools: `query_order_status, query_inventory_by_sku, query_purchase_arrival, query_exception_sop`
- permission: `query_order_status=allowed, query_inventory_by_sku=allowed, query_purchase_arrival=allowed, query_exception_sop=allowed`
- risk_level: `high`
- business_conclusion: 订单 O1001 暂不建议自动发货，库存不足或需复核，can_ship=False, partial_ship=True, shortage_risk=high, delivery_delay_risk=high. 采购单 PO1001 状态 delayed，预计到货 2026-06-28。
- agent_call_id: `7`

answer:

```text
路由意图: 订单发货风险分析 (order_delivery_risk)
分析路径: identify_order -> query_order_status -> query_inventory -> query_purchase_arrival -> query_exception_sop -> compose_answer
检查数据: 销售订单 | 销售订单明细 | SKU 库存 | 采购到货 | 交期异常 SOP
调用工具: query_order_status(allowed) | query_inventory_by_sku(allowed) | query_purchase_arrival(allowed) | query_exception_sop(allowed)
业务结论: 订单 O1001 暂不建议自动发货，库存不足或需复核，can_ship=False, partial_ship=True, shortage_risk=high, delivery_delay_risk=high. 采购单 PO1001 状态 delayed，预计到货 2026-06-28。
建议下一步: Do not complete shipment automatically; review shortage: SKU-KB-001 shortage 40. Quality owner should review held inventory before shipment commitment. Purchase should confirm delayed arrival and sales should communicate delivery risk. Production should confirm work order replenishment timing before promise date. SOP 建议参考：# 订单库存不足与交期异常处理 SOP

适用范围：销售订单因可用库存不足、锁定库存不足、采购到货延期或批次异常导致暂不建议发货时的处理。

## 处理步骤

1. 销售确认客户订单号、SKU、需求数量、计划交付日期和客户优先级。
2. 仓库复核 SKU 可用库存、锁定库存、批次状态、仓库编码和是否存在质量冻结批次。
3. 采购确认相关采购单预计到货日期、延
人工确认: Risky business actions require human confirmation in the enterprise system.
```
