# 采购延期影响模型

当前模型用于分析模拟采购单延期对客户订单的影响。它只读取采购、销售订单和 SOP 数据，不执行催单、改交期、审批或客户通知。

## 输入

- 采购单号，如 `PO1001`。
- 采购明细 SKU、采购数量、已到货数量。
- 采购单预计到货日期和延期状态。
- 使用相同 SKU 的销售订单。

## 判断逻辑

1. 查询采购单和采购明细。
2. 如果采购单不存在，返回 `business_identifier_not_found`。
3. 如果采购单延期，按采购 SKU 查找相关销售订单。
4. 找到相关客户订单时，`manual_review_reason` 包含 `purchase_delay`。
5. 未找到相关客户订单时，仍提示采购跟踪到货，但风险较低。
6. 查询采购延期沟通 SOP 作为建议依据。

## 输出

- 受影响客户订单列表或说明。
- `risk_factors`
- `evidence`
- `recommendations`
- `requires_human_review`
- `manual_review_reason`

模型只给出影响分析和人工沟通建议，不直接修改采购或销售订单。
