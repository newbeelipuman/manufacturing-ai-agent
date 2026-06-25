# 诺必达 JD 项目简历 Bullet

项目描述：

设计并实现制造业企业 AI Agent 全栈 MVP，覆盖 React 管理台、FastAPI 后端、自然语言业务查询、Agent 工具编排、RAG 知识库、JWT/RBAC、权限申请审批、审计日志、用量统计、mock LLM Gateway、Docker/Nginx 本地全栈部署和云服务器部署准备；模拟 ERP/MES/WMS 数据，实现订单发货风险、工单齐套、采购延期影响、库存批次和异常 SOP 查询等场景。

可用于简历的事实 bullet：

- 基于 FastAPI、SQLAlchemy、Pydantic 实现制造业企业 AI Agent 后端 MVP，支持 `/api/chat` 自然语言查询和只读工具编排。
- 基于 React、TypeScript、Vite 实现企业后台控制台，覆盖 Chat 工作台、Admin Dashboard、Audit Logs、Knowledge Search、Permission Center、Approval Center 和 Deployment Status。
- 实现 demo JWT 登录与服务端 RBAC，覆盖菜单级、API 级、文档级和 Agent 工具级权限；兼容旧 `role` 参数，并在 token 存在时以 token 身份为准。
- 实现平台权限申请与 admin 审批流，审批通过写入用户权限授权并影响菜单可见性；申请和审批写入审计日志，明确不属于订单、采购、出库等业务审批。
- 设计销售订单、库存批次、工单、采购单、SOP 知识、审计日志、用量统计等模拟 ERP/MES/WMS 数据模型。
- 实现角色权限矩阵，所有工具调用前先校验权限，并将允许、拒绝和失败写入 `tool_call_log`。
- 为 Agent 响应增加 `decision_record`、风险因子、人工复核原因和 execution trace，便于面试演示企业级治理思路。
- 实现轻量本地 RAG 检索，返回 `source_path`、`score`、`matched_terms`，并提供 `run_rag_eval.py` 生成评估报告。
- 增加 mock LLM Gateway / model routing，记录 provider、model、token 估算和 latency，不依赖外部 API key。
- 提供 Docker Compose、Nginx 前端静态托管与 `/api` 反代、本地全栈部署文档、云服务器购买与部署 runbook，便于说明企业内网或云服务器演示部署路径。
- 增加 request id middleware、`/api/admin/metrics`、CI 检查脚本和观测性检查报告，支持本地运行 compileall、pytest、前端 smoke/build、compose config、demo report 和 RAG eval。

边界说明：

本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
