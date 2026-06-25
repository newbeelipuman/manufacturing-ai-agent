# RAG Eval Report

Generated at: 2026-06-25 12:35:27

本报告由 `python scripts/run_rag_eval.py` 生成。评估使用本地模拟 SOP 文档和轻量 TF-IDF 风格检索，不调用外部 LLM。

| query | expected_source | top_source | score | matched_terms | passed |
| --- | --- | --- | ---: | --- | --- |
| 注塑件外观不良应该怎么处理？ | `docs/sop/injection_appearance_exception.md` | `docs/sop/injection_appearance_exception.md` | 3.8326 | 注塑件, 外观不良 | True |
| 采购延期应该怎么沟通？ | `docs/sop/purchase_delay_communication.md` | `docs/sop/purchase_delay_communication.md` | 3.1394 | 采购延期, 沟通 | True |
| 订单库存不足导致不能发货怎么办？ | `docs/sop/order_delivery_exception.md` | `docs/sop/order_delivery_exception.md` | 1.5108 | 库存不足 | True |
| 工单缺料不能开工怎么办？ | `docs/sop/work_order_material_shortage.md` | `docs/sop/work_order_material_shortage.md` | 5.3434 | 工单缺料, 缺料, 开工 | True |
| 订单交期异常应该怎么处理？ | `docs/sop/order_delivery_exception.md` | `docs/sop/order_delivery_exception.md` | 1.9163 | 交期异常 | True |

Passed: 5/5

边界：当前仍是 MVP 原型，知识来源为本地模拟 SOP，不接入真实企业知识库或 ERP/MES/WMS。