# 诺必达 AI 全栈 / SaaS-ready 下一阶段执行计划

## 目标

在现有制造业企业 AI Agent 后端 MVP 基础上，补齐两个最明显短板：

1. React 前端 / 全栈交付证据不足。
2. 真实上线 / SaaS 实战证据不足。

同时按更苛刻的企业系统要求，增强：

- JWT 登录与服务端鉴权。
- RBAC 菜单、页面、API、文档、Agent 工具权限。
- 权限申请与管理员审批。
- 前后端 Docker/Nginx 一体化部署。
- 云服务器部署验证证据链。
- CI、观测性、错误处理、测试报告。

本阶段仍必须保持事实边界：

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

权限申请、菜单配置、用户登录、审批权限申请属于平台管理数据，不是 ERP/MES/WMS 业务写操作。不得实现自动出库、调账、订单审批、采购下单、工单开工等写侧业务动作。

## 调研摘要

### React / Vite

- React 官方建议从 Vite、Parcel、Rsbuild 等构建工具开始，它们提供本地开发服务和生产构建能力。
- Vite 官方说明 `build` 命令会输出优化后的静态资源，适合由 Nginx 托管。

参考：

- https://react.dev/learn/build-a-react-app-from-scratch
- https://vite.dev/guide/

### JWT / RBAC

- FastAPI 官方 OAuth2/JWT 教程说明可用 scopes 给 token 绑定受限权限集合。
- JWT 只解决“用户是谁 / token 是否可信”，真正的菜单、页面、API、文档、工具权限应由服务端 RBAC 权限表和依赖校验实现。
- OWASP Authorization Cheat Sheet 强调授权逻辑应符合业务上下文、可维护、可扩展，并应在服务端强制执行。

参考：

- https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html
- https://owasp.org/www-community/Access_Control

### 云服务器 / Docker

- Docker 官方文档支持在 Ubuntu 22.04 LTS 和 24.04 LTS 等版本安装 Docker Engine。
- 下一阶段云服务器应先完成本地前后端 Docker/Nginx 整合，再购买服务器部署，避免服务器空跑和返工。

参考：

- https://docs.docker.com/engine/install/ubuntu/

## 当前项目状态

已完成：

- FastAPI 后端。
- `/api/chat` 规则路由、工具编排、权限预检查。
- 5 个核心 demo 问题。
- 模拟 ERP/MES/WMS 数据。
- 角色权限、审计日志、usage stats。
- RAG 检索、score、matched_terms、RAG eval report。
- mock LLM Gateway。
- Docker Compose、PostgreSQL、Redis、Nginx。
- 私有化部署文档和 deployment check report。
- JD 简历 bullet 和面试答辩材料。

仍不足：

- 没有 React 前端，不能证明“全栈交付”。
- 认证仍偏 demo，`role` 参数可伪造，不像真实企业系统。
- 权限粒度不够细，缺少菜单级、页面级、API 级、文档级控制。
- 缺少“用户申请权限，管理员审批”的企业工作流。
- 没有前后端一体化 Nginx 静态托管与 `/api` 反代。
- 没有真实云服务器部署验证。
- CI、观测性、前端 smoke test 还不够完整。

## 总体执行顺序

严格按以下顺序推进：

1. P8 React 全栈控制台。
2. P9 JWT + RBAC 权限系统。
3. P10 权限申请与管理员审批。
4. P11 本地前后端 Docker/Nginx 一体化。
5. P12 云服务器购买与部署验证。
6. P13 CI / 观测性 / 最苛刻补强。
7. P14 简历与面试材料二次更新。

不要一开始就买服务器。先完成本地前后端一体化并通过构建，再购买云服务器部署。

## P8：React 全栈控制台

目标：补足“AI 全栈 / 应用工程师”中的前端交付证据。

### 技术选择

- 新增 `frontend/`。
- React + TypeScript + Vite。
- UI 风格：企业后台控制台，不做营销页。
- 首屏直接是工作台或登录页。
- 前端只调用现有 API，不直接读写数据库。

### 页面

必须包含：

- 登录页。
- Chat 工作台：
  - 选择角色或使用登录态。
  - 输入问题。
  - 展示 answer、called tools、permission results、risk factors、manual review reason、decision record。
- Admin Dashboard：
  - usage stats。
  - success rate。
  - denied rate。
  - avg latency。
  - top tools。
  - top intents。
- Audit Logs：
  - agent call logs。
  - tool call logs。
  - call detail。
- Knowledge Search：
  - query。
  - doc title。
  - source path。
  - score。
  - matched terms。
- Permission Center：
  - 当前用户权限。
  - 申请权限。
  - 申请历史。
- Admin Approval Center：
  - pending permission requests。
  - approve / reject。
- Deployment Status：
  - health check。
  - demo report。
  - rag eval report。

### 验收

- `cd frontend && npm install`
- `npm run build`
- 至少新增前端 smoke test 或 Playwright 截图验证。
- normal_user 看不到 admin 菜单。
- admin 能访问 dashboard 和 logs。
- README 增加前端本地启动和构建步骤。

## P9：JWT + RBAC 权限系统

目标：从 demo role 参数升级为更接近企业系统的鉴权与授权模型。

### 后端新增模型

建议新增：

- `AuthUser`
- `Role`
- `Permission`
- `RolePermission`
- `UserRole`
- `UserPermissionGrant`，可选，用于审批后的个体临时授权。
- `MenuPermission`
- `ApiPermission`
- `DocumentPermission`

如果时间有限，先实现角色绑定权限即可；个体权限只做 `UserPermissionGrant` 的轻量补充，不做复杂组织架构。

### 后端新增 API

- `POST /api/auth/login`
- `GET /api/auth/me`
- `GET /api/auth/permissions`
- `GET /api/menus`

### 权限粒度

必须覆盖：

- 菜单级：能不能看到菜单。
- 页面级：能不能进入页面。
- API 级：能不能调用接口。
- 文档级：能不能搜索或查看某类 SOP。
- Agent 工具级：沿用现有工具权限矩阵。

### JWT 设计

Token 可包含：

- `sub`
- `username`
- `role`
- `exp`
- `jti`

权限不要完全信任前端，后端每个敏感 API 必须重新校验。

### 兼容策略

- 保留现有 `role` 参数兼容旧测试。
- 新前端优先使用 `Authorization: Bearer <token>`。
- 如果 token 和 role 参数同时存在，以 token 身份为准。

### 验收

- 未登录不能访问前端工作台。
- normal_user 调 admin API 被拒绝。
- sales 不能看 admin logs。
- admin 能看全部后台。
- 后端接口不依赖前端隐藏，必须真实拦截。
- pytest 覆盖 login、me、admin denied、menu permission。

## P10：权限申请与管理员审批

目标：补足企业系统中“权限不是随便给，申请要审批”的工作流。

### 后端新增模型

- `PermissionRequest`
  - id
  - requester_username
  - requested_permission
  - requested_role，可选
  - reason
  - status: pending / approved / rejected
  - approver_username
  - approval_comment
  - created_at
  - decided_at

### 后端新增 API

- `POST /api/permissions/requests`
- `GET /api/permissions/requests/my`
- `GET /api/admin/permission-requests`
- `POST /api/admin/permission-requests/{request_id}/approve`
- `POST /api/admin/permission-requests/{request_id}/reject`

### 前端页面

- 普通用户：
  - 查看当前权限。
  - 提交权限申请。
  - 查看申请状态。
- admin：
  - 查看待审批列表。
  - 审批通过。
  - 审批拒绝。

### 边界

审批的是“平台访问权限”，不是业务审批。不得实现订单审批、采购审批、出库审批等业务写动作。

### 验收

- normal_user 申请查看 usage dashboard。
- admin 审批通过后，normal_user 可看到对应菜单或功能。
- admin 拒绝后，normal_user 仍不可访问。
- 所有申请和审批写入审计日志。

## P11：本地前后端 Docker/Nginx 一体化

目标：买云服务器前先把部署结构定死。

### 改造

- 前端 `npm run build` 输出静态文件。
- Nginx 托管前端静态文件。
- Nginx 反代 `/api` 到 backend。
- Nginx 反代 `/health` 或 `/api/health` 到 backend。
- Docker Compose 包含：
  - nginx/frontend
  - backend
  - postgres
  - redis

### 文档

新增：

- `docs/frontend-deployment.md`
- `docs/local-fullstack-deployment-check-report.md`

### 验收

- `npm run build`
- `docker compose config`
- `docker compose up -d --build`
- 浏览器访问 `http://localhost:8080`
- `http://localhost:8080/health` 正常。
- 前端登录正常。
- 前端 Chat 能调用 `/api/chat`。

## P12：云服务器购买与部署验证

目标：补“真实云服务器部署验证”证据，但不宣称生产落地。

### 购买建议

推荐：

- 2 核 4G。
- Ubuntu 22.04 LTS 或 24.04 LTS。
- 40GB SSD 起。
- 3Mbps 起。
- 安全组开放：
  - 22 SSH。
  - 80 HTTP。
  - 443 HTTPS，后续需要域名时再开。
  - 8080 仅临时调试，不建议长期暴露。

预算紧张可用：

- 2 核 2G。

但 2G 内存同时跑 PostgreSQL、Redis、backend、Nginx、构建前端可能吃紧。推荐本地构建镜像或选择 2 核 4G。

### 部署步骤

新增：

- `docs/cloud-server-buying-guide.md`
- `docs/cloud-deployment-runbook.md`
- `docs/cloud-deployment-check-report.md`

云部署流程：

1. 购买服务器。
2. 初始化 Ubuntu。
3. 安装 Docker Engine。
4. 配置安全组。
5. 拉取代码。
6. 配置 `.env.production`。
7. `docker compose config`
8. `docker compose up -d --build`
9. `docker compose exec backend python -m app.db.init_db`
10. `docker compose exec backend python scripts/seed_demo_data.py`
11. 验证 `http://<server-ip>/health`
12. 验证前端登录。
13. 验证 `/api/chat`。
14. 写入 cloud deployment check report。

### 简历边界

可写：

```text
使用云服务器完成 Docker Compose 部署验证，Nginx 托管 React 前端并反代 FastAPI API，PostgreSQL 持久化模拟业务数据，形成可复现部署文档和检查报告。
```

不可写：

```text
生产级上线。
真实企业部署。
真实 ERP 接入。
企业客户已使用。
```

## P13：CI / 观测性 / 最苛刻补强

目标：让项目更像“能维护的 SaaS / AI 平台”。

### CI

新增：

- `.github/workflows/ci.yml` 或 `scripts/run_ci_checks.py`

CI 内容：

- backend compileall。
- pytest。
- frontend typecheck。
- frontend build。
- docker compose config。
- run_demo_report。
- run_rag_eval。

### 观测性

新增：

- request id middleware。
- 所有 agent/tool logs 增加 request_id。
- `/metrics` 或 `/api/admin/metrics`。

指标：

- total requests。
- total agent calls。
- total tool calls。
- success rate。
- denied rate。
- avg latency。
- high risk count。

### 前端质量

新增：

- loading 状态。
- error 状态。
- token expired 处理。
- 403 权限提示。
- 404 页面。
- Playwright smoke test。

### 验收

- CI 命令本地可运行。
- metrics API 可访问。
- request_id 能串起 agent log 和 tool log。
- 前端 smoke test 通过。

## P14：简历与面试材料二次更新

目标：把新增能力转成可信简历表达。

更新：

- `docs/resume-project-bullets-nuobida.md`
- `docs/interview-answer-nuobida.md`
- `docs/interview-walkthrough.md`
- README

新增表达方向：

```text
设计并实现制造业企业 AI Agent 全栈 MVP，包含 FastAPI 后端、React 管理台、Agent 工具编排、RAG 检索、JWT/RBAC、权限申请审批、审计日志、用量统计、mock LLM Gateway、Docker/Nginx 云服务器部署验证和 CI 质量门禁；项目使用模拟 ERP/MES/WMS 数据，不接入真实生产系统，所有业务工具保持只读。
```

必须同时保留边界说明：

```text
本项目为 MVP 原型，使用模拟 ERP/MES/WMS 数据，不接入真实企业生产系统。
Agent 工具全部为只读查询或分析工具，不执行出库、调账、审批、下单等业务写操作。
后续接入真实企业系统时，可将模拟接口替换为真实 API、数据库视图或中间表。
```

## 下个对话建议目标

可以直接使用：

```text
/goal 以 G:\manufacturing-ai-agent\docs\nuobida-fullstack-saas-next-phase-plan.md 为唯一执行基准，完成 P8-P14：React 全栈控制台、JWT/RBAC、权限申请审批、本地前后端 Docker/Nginx 一体化、云服务器部署准备与验证、CI/观测性补强、简历面试材料更新。保持只读业务边界，不接真实 ERP/MES/WMS，不执行任何写侧业务动作，不伪造生产落地结果。先实现 P8，再按计划顺序推进；每阶段必须有测试、构建或报告验证。
```

如果准备先买服务器，可在 P11 完成本地前后端一体化后再买；买之前先确认：

- 是否能接受 2 核 4G 成本。
- 是否需要域名和 HTTPS。
- 是否只是公网 IP 演示。
- 是否使用 Ubuntu 22.04 LTS。

## 总体验收命令

后端：

```bash
python -m compileall app
pytest
python scripts/run_demo_report.py
python scripts/run_rag_eval.py
docker compose config
```

前端：

```bash
cd frontend
npm install
npm run build
```

部署：

```bash
docker compose up -d --build
curl http://localhost:8080/health
```

云服务器部署后：

```bash
curl http://<server-ip>/health
```

最终必须生成或更新：

- README。
- `docs/frontend-deployment.md`
- `docs/local-fullstack-deployment-check-report.md`
- `docs/cloud-server-buying-guide.md`
- `docs/cloud-deployment-runbook.md`
- `docs/cloud-deployment-check-report.md`
- `docs/ci-cd-check-report.md`
- `docs/resume-project-bullets-nuobida.md`
- `docs/interview-answer-nuobida.md`
