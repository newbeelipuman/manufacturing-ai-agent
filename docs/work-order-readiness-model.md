# 工单齐套模型

当前模型用于判断模拟工单是否具备开工前齐套条件。它只读取工单、用料和库存数据，不执行领料、开工、调账或排产写入。

## 输入

- 工单号，如 `WO1001`。
- 工单产品、计划数量、计划日期。
- 工单用料需求和已领数量。
- 物料 SKU 可用库存。

## 判断逻辑

1. 查询工单和用料清单。
2. 对每个物料计算 `required_remaining = required_quantity - issued_quantity`。
3. 查询物料库存。
4. 如果 `required_remaining > available_quantity`，记录缺料。
5. 有缺料时返回 `risk_level=high`，`manual_review_reason` 包含 `work_order_material_shortage`。
6. 无缺料时只提示开工前仍需人工复核设备、人员和领料状态。

## 输出

- `risk_factors`
- `evidence`
- `recommendations`
- `requires_human_review`
- `manual_review_reason`

模型不会自动开工或自动领料。
