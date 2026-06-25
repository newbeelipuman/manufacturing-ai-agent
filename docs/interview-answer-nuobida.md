# 诺必达 AI 全栈 / 应用工程师面试答辩

## 为什么不是普通 RAG？

项目不是只把问题丢给知识库检索。`/api/chat` 会先做意图识别和实体抽取，再生成工具计划，执行权限预检查，调用只读业务工具或 SOP 检索，最后返回业务结论、证据、风险因子、人工复核原因和 `decision_record`。RAG 只负责 SOP 类知识，不替代订单、库存、工单、采购等结构化业务查询。

## 为什么不接真实 ERP？

当前项目定位是求职演示 MVP。为了保持安全和事实边界，数据使用模拟 ERP/MES/WMS 表，不连接真实企业生产系统。真实接入时可以把工具层替换为真实 API、数据库视图或中间表，同时保留权限、审计和只读边界。

## 为什么工具只读？

订单发货、调账、审批、下单、开工等动作属于高风险业务写操作。MVP 中 Agent 只做查询、分析和建议，所有高风险结论都返回 `requires_human_review` 和 `manual_review_reason`，提醒业务人员在企业系统中人工确认。

## 如何接 OpenAI / Claude / 私有模型？

当前 `llm_gateway_service.py` 是 mock gateway，会输出 provider、model、fallback model、token 估算和 latency。后续可在这一层接 OpenAI、Claude 或私有模型，并保留统一路由、fallback、审计和用量统计。业务结论仍应由 deterministic orchestration 和只读工具结果约束。

## 如何部署到企业内网？

项目提供 Docker Compose、PostgreSQL、Redis、FastAPI backend、Nginx 托管 React 前端和 `.env.production.example`。本地全栈部署时，Nginx 服务 React SPA，并把 `/api`、`/health` 反代到 backend。私有化或云服务器验证流程包括 Ubuntu 22.04/24.04 准备、配置 `.env.production`、`docker compose config`、`docker compose up -d --build`、初始化数据库、seed 模拟数据、验证 `/health`、前端登录和 `/api/chat`。

## 如何保证权限和审计？

工具调用统一走 `execute_tool`，先检查角色权限，再执行只读函数。允许、拒绝、失败都会写入 `tool_call_log`。每次 Agent 调用写入 `agent_call_log`，其中包含 `decision_record`、执行路径、权限结果、工具摘要、风险结果和最终结论。P9 后新增 JWT 登录和 RBAC，覆盖菜单、API、文档和 Agent 工具权限；P10 后新增权限申请与 admin 审批，审批的是平台访问权限，不是业务审批。Admin 可以查看调用详情、usage stats 和 metrics。

## 前端做了什么？

前端使用 React、TypeScript、Vite，实现企业后台控制台而不是营销页。页面包括 Chat 工作台、Admin Dashboard、Audit Logs、Knowledge Search、Permission Center、Admin Approval Center 和 Deployment Status。前端通过 `/api/auth/login` 获取 token，调用后端 API，normal_user 看不到 admin 菜单，admin 可以访问 dashboard 和 logs；Chat 工作台会展示 answer、工具权限、risk factors、manual review reason 和 decision record，Audit Logs 会读取 agent/tool log 列表并拉取 agent call detail，Knowledge Search 展示 SOP title/source/score/matched terms，Deployment Status 调用 `/health`。normal_user 可以提交平台权限申请，admin 可以审批 pending permission requests。服务端菜单缺少 `chat` 时不会错误回退，已登录请求收到 401 时会回到登录页，API 返回 403 时会展示无权限提示，未知路由会显示 404 页面。前端有 smoke test 和生产 build 验证。

## CI 和观测性做了什么？

后端增加 request id middleware，响应头返回 `x-request-id`，并把 request id 写入 `agent_call_log` 和 `tool_call_log`，方便串联一次请求的 Agent 和工具调用。新增 `/api/admin/metrics` 返回 total requests、agent/tool calls、success rate、denied rate、avg latency 和 high risk count。`scripts/run_ci_checks.py` 聚合 backend compileall、pytest、frontend smoke/build、docker compose config、demo report 和 RAG eval。

## 当前限制是什么？

- 当前是 MVP 原型，不接真实 ERP/MES/WMS。
- RAG 使用本地轻量评分，不调用外部 embedding 或 LLM。
- LLM Gateway 是 mock provider。
- 没有多租户、Kubernetes、真实云服务器执行证据或复杂 CI/CD 平台；当前提供本地 CI 脚本和云部署 runbook。
- 只覆盖计划中的制造业演示问题和核心扩展场景。
