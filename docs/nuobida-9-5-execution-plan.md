# 诺必达 AI 全栈 / 应用工程师 9.5 分匹配执行计划

## 目标

将 `manufacturing-ai-agent` 从“制造业 Agent Demo”升级为“制造业企业 AI Agent 平台后端 MVP”，尽可能贴近诺必达 AI 全栈 / 应用工程师 JD。

目标岗位关键词：

- 企业 AI 转型
- 企业级 Agent / 工具调用
- 大模型网关 / 路由
- Agent 编排
- RAG / 知识库
- 权限与安全
- 用量管理
- 后端开发、API 设计
- Docker、Nginx、Linux / 私有云部署
- 制造业业务场景

本项目必须保持事实边界：

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

不要写“生产级落地”“真实企业已部署”“真实 ERP 已接入”“效率提升百分比”“成本下降百分比”等无法验证表述。

## 当前状态摘要

已具备：

- FastAPI 后端和 `/health`。
- SQLAlchemy 模型。
- SQLite 本地 fallback，Docker Compose PostgreSQL 演示环境。
- 模拟 ERP/MES/WMS 数据。
- 5 个基础只读工具。
- `/api/chat` 规则路由、实体抽取、工具计划、复合分析。
- 角色权限、审计日志、用量统计。
- SOP 知识检索。
- Docker Compose、Nginx。
- `scripts/run_demo_report.py` 和 `docs/demo-report.md`。
- `docs/interview-walkthrough.md`。
- `docs/target-jd-nuobida-ai-fullstack.md`。

主要短板：

- Agent 决策记录还不够稳定。
- human-in-the-loop 字段不足。
- usage stats 没有日期过滤、成功率、拒绝率、平均延迟等指标。
- SOP 检索仍偏关键词，缺少更可信的 score / matched terms / eval report。
- 缺少 mock LLM Gateway / model routing 模块。
- 部署文档还不够像私有化上线证据链。
- 制造业业务深度还可以再增强。
- 缺少面向该 JD 的简历 bullet 和面试答辩材料。

## 执行顺序

严格按以下顺序推进。不要先做前端，不要先做真实 LLM，不要先做复杂 CI/CD。

1. P5 Agent 治理增强。
2. P6 RAG 可信度增强。
3. 部署运维证据链。
4. mock LLM Gateway / model routing。
5. P7 制造业业务深度。
6. JD 简历与面试材料。

每一阶段都必须保持测试可运行。不要做大范围重构。

## P5：Agent 治理增强

目标：让项目像“企业级 Agent 后端”，不是普通工具调用 demo。

### 要改的行为

`/api/chat` 响应增加：

- `decision_record`
- `risk_factors`
- `requires_human_review`
- `manual_review_reason`

`AnalysisResponse` 增加：

- `risk_factors`
- `requires_human_review`
- `manual_review_reason`

`agent_call_log.response_json` 稳定保存：

- `decision_record.plan`
- `decision_record.permission_results`
- `decision_record.tool_result_summary`
- `decision_record.risk_result`
- `decision_record.llm_route`
- `decision_record.final_decision`

高风险或阻断场景必须设置：

- `requires_human_review=true`
- 明确 `manual_review_reason`

触发人工复核的原因至少覆盖：

- `inventory_shortage`
- `purchase_delay`
- `permission_denied`
- `quality_hold`
- `work_order_material_shortage`
- `business_identifier_not_found`
- `clarification_required`

### usage stats 增强

`GET /api/admin/usage-stats?role=admin` 增强为支持：

- `date_from=YYYY-MM-DD`
- `date_to=YYYY-MM-DD`
- `success_rate`
- `denied_rate`
- `avg_latency_ms`
- `top_tools`
- `top_intents`

保留现有字段，避免打破旧测试。

### 管理详情接口增强

`GET /api/admin/agent-call-logs/{call_id}?role=admin` 返回：

- `decision_record`
- `response_json`
- `tool_calls`
- `execution_trace`

### P5 验收

必须新增或更新测试，覆盖：

- high risk 订单发货风险返回 `requires_human_review=true`。
- normal_user 查询订单被拒绝，`manual_review_reason` 包含 `permission_denied`。
- admin call detail 能看到 `decision_record`。
- usage stats 日期过滤有效。
- usage stats 返回 success rate、denied rate、avg latency、top tools、top intents。

## P6：RAG 可信度增强

目标：让“知识库 / RAG”说法站得住，不只是关键词命中。

### 检索实现

保持轻量依赖，不接外部 LLM。优先实现本地 BM25 / TF-IDF 风格评分。

每个结果返回：

- `doc_title`
- `source_path`
- `chunk_index`
- `score`
- `matched_terms`
- `chunk_text`

`query_exception_sop` 和 `/api/knowledge/search` 都使用同一套检索逻辑，避免两套结果不一致。

### RAG eval

新增 `scripts/run_rag_eval.py`。

生成 `docs/rag-eval-report.md`。

评测问题至少包含：

```text
注塑件外观不良应该怎么处理？
采购延期应该怎么沟通？
订单库存不足导致不能发货怎么办？
工单缺料不能开工怎么办？
订单交期异常应该怎么处理？
```

报告每个 case 输出：

- query
- expected_source
- top_source
- score
- matched_terms
- passed

### P6 验收

必须新增或更新测试，覆盖：

- SOP 查询返回 `source_path`、`score`、`matched_terms`。
- normal_user 可以查询 SOP。
- normal_user 仍不能查询订单、库存、工单、采购。
- `python scripts/run_rag_eval.py` 可运行并生成 report。

## 部署运维证据链

目标：对齐 JD 里的 Linux、Docker、Nginx、云服务器或私有云环境。

### 文档与模板

新增：

- `docs/deployment-private-cloud.md`
- `.env.production.example`
- `docs/deployment-check-report.md`

`docs/deployment-private-cloud.md` 必须包含：

- Ubuntu 22.04 服务器准备。
- Docker / Docker Compose 安装检查。
- 获取代码。
- 配置 `.env`。
- `docker compose config`。
- `docker compose up -d --build`。
- PostgreSQL 初始化。
- seed demo 数据。
- Nginx 反代入口。
- `/health` 验证。
- `/api/chat` 验证。
- `docker compose ps`。
- `docker compose logs backend`。
- 常见故障排查。

`.env.production.example` 必须提醒：

- 必须修改默认数据库密码。
- 不提交真实 `.env`。
- 当前仍是 MVP demo，不接真实 ERP/MES/WMS。

`docs/deployment-check-report.md` 必须真实记录当前验证状态。不能伪造云服务器部署结果。

### 部署验收

必须执行：

```bash
docker compose config
```

如果 Docker Desktop / Docker Engine 可用，再执行：

```bash
docker compose up -d --build
docker compose exec backend python -m app.db.init_db
docker compose exec backend python scripts/seed_demo_data.py
curl http://localhost:8080/health
```

如果 Docker 不可用，在 report 中写明未执行原因和待执行命令。

## mock LLM Gateway / Model Routing

目标：补上 JD 中“大模型网关 / 路由”的平台化影子，但不真实调用外部模型。

### 新增 service

新增 `app/services/llm_gateway_service.py`。

默认 mock provider。

输入：

- question
- intent
- role
- provider
- model

输出：

- `provider`
- `model`
- `fallback_model`
- `mode`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `latency_ms`
- `used_fallback`

token 使用字符长度近似估算即可，不接真实 tokenizer。

### 配置

在配置中增加：

- `LLM_GATEWAY_MODE=mock`
- `LLM_PROVIDER=mock`
- `LLM_MODEL=mock-enterprise-agent`
- `LLM_FALLBACK_MODEL=mock-safe-fallback`

写入 `.env.example` 和 `.env.production.example`。

### 集成

`/api/chat` 每次调用生成一条 `llm_route`，放入：

- response `decision_record.llm_route`
- `agent_call_log.model_name`
- `agent_call_log.estimated_prompt_tokens`
- `agent_call_log.estimated_completion_tokens`

不要让 mock LLM 决定业务结论。业务结论仍由 deterministic orchestration 和只读工具决定。

### mock Gateway 验收

测试覆盖：

- `/api/chat` response decision record 中有 `llm_route`。
- `agent_call_log` 写入 model name 和 token 估算。
- 不需要外部 API key。
- 断网也能运行。

## P7：制造业业务深度

目标：让项目体现制造业业务理解，而不是通用 Agent 壳。

### 订单发货风险

覆盖：

- 库存不足。
- 库存充足。
- 质量冻结批次。
- 采购延期。
- 工单补货影响。

输出：

- `risk_factors`
- `evidence`
- `recommendations`
- `manual_review_reason`

### 工单齐套

覆盖：

- 缺料。
- 不缺料。
- 供应商延期影响开工。

### 采购延期影响

覆盖：

- 影响客户订单。
- 暂未影响客户订单。

### 业务模型文档

新增或更新：

- `docs/order-shipment-risk-model.md`
- `docs/work-order-readiness-model.md`
- `docs/purchase-delay-impact-model.md`

文档必须和代码逻辑一致。

### P7 验收

测试覆盖：

- 订单 O1001 高风险原因包含库存不足、质量冻结或采购延期。
- 工单 WO1001 缺料路径包含 `work_order_material_shortage`。
- 采购单 PO1001 延期影响 O1001。
- 所有高风险结论不执行写操作，只返回人工复核建议。

## JD 简历与面试材料

目标：让 HR、AI 简历筛选和面试官都能看到 JD 匹配度。

新增：

- `docs/resume-project-bullets-nuobida.md`
- `docs/interview-answer-nuobida.md`

项目描述建议：

```text
设计并实现制造业企业 AI Agent 后端 MVP，覆盖自然语言业务查询、Agent 工具编排、RAG 知识库、角色权限、审计日志、用量统计、Docker/Nginx 私有化部署；模拟 ERP/MES/WMS 数据，实现订单发货风险、工单齐套、采购延期影响、库存批次和异常 SOP 查询等场景。
```

面试材料必须覆盖：

- 为什么不是普通 RAG？
- 为什么不接真实 ERP？
- 为什么工具只读？
- 如何接 OpenAI / Claude / 私有模型？
- 如何部署到企业内网？
- 如何保证权限和审计？
- 当前限制是什么？

## 总体验收命令

每个阶段完成后至少执行：

```bash
python -m compileall app
pytest
docker compose config
```

P4/P5/P7 后执行：

```bash
python scripts/run_demo_report.py
```

P6 后执行：

```bash
python scripts/run_rag_eval.py
```

最终 README 必须包含：

- 项目定位。
- JD 对齐能力说明。
- 架构图。
- 快速启动。
- Docker / 私有化部署入口。
- Demo report。
- RAG eval report。
- 当前边界。
- 不接真实企业系统、不执行写侧业务动作的边界 wording。

## 禁止事项

不要做：

- 真实 ERP/MES/WMS 接入。
- 真实业务写操作。
- 自动出库、自动调账、自动审批、自动下单。
- 夸大生产级落地。
- 复杂前端。
- Kubernetes。
- 真实 LLM API 强依赖。
- 破坏现有 5 个必答 demo 问题。

业务工具名前缀只允许：

- `query_`
- `search_`
- `get_`
- `analyze_`

禁止新增以下业务工具名前缀：

- `create_`
- `update_`
- `delete_`
- `approve_`
- `submit_`
- `adjust_`
- `outbound_`
- `issue_`
- `write_`

## 最终完成定义

当且仅当以下条件都满足，才算本计划完成：

- 5 个必答 demo 问题仍可通过 `/api/chat` 跑通。
- 每个回答包含数据检查、工具调用、权限结果、业务结论、建议下一步、人工确认提醒。
- high risk / blocked 场景有 `requires_human_review` 和 `manual_review_reason`。
- admin 能查看完整 decision record。
- RAG 查询有 source、score、matched_terms。
- RAG eval report 已生成。
- Docker Compose config 通过。
- 私有化部署文档和检查报告已生成。
- mock LLM Gateway 有 route 和 token/latency 记录。
- README 和 JD 面试材料完成。
- 测试通过。
