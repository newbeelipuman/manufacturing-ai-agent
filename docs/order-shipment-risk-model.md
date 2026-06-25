# 订单发货风险模型

当前模型用于 MVP 演示，只读取模拟销售订单、库存、采购和工单数据，不执行发货、锁库、调账或客户承诺。

## 输入

- 销售订单号，如 `O1001`。
- 订单明细需求数量和已发数量。
- SKU 可用库存、锁定库存、质量冻结库存。
- 相关采购单预计到货和延期状态。
- 相关工单补货计划。

## 判断逻辑

1. 查询销售订单和明细。
2. 对每个 SKU 计算 `demand = quantity - delivered_quantity`。
3. 读取库存，计算 `usable_inventory = max(available_quantity - quality_hold_quantity, 0)`。
4. 如果 `demand > usable_inventory`，记录 `inventory_shortage`。
5. 如果存在 `quality_hold_quantity > 0`，记录 `quality_hold`。
6. 如果相关采购单延期，记录 `purchase_delay`。
7. 如果存在未完工补货工单，记录补货证据和人工复核建议。

## 输出

- `risk_factors`
- `evidence`
- `recommendations`
- `requires_human_review`
- `manual_review_reason`

高风险结论只返回人工复核建议，不执行写侧业务动作。
