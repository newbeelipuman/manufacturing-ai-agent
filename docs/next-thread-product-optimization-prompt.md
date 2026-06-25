# 下个对话提示词：产品体验与权限审计优化

请先读取这些文件：

1. `G:\manufacturing-ai-agent\AGENTS.md`
2. `G:\manufacturing-ai-agent\docs\thread-2026-06-25-cloud-and-product-ux-summary.md`
3. `G:\manufacturing-ai-agent\docs\p15-product-hardening-backlog.md`
4. `G:\manufacturing-ai-agent\docs\cloud-server-first-deployment-experience.md`
5. `G:\manufacturing-ai-agent\docs\next-thread-handoff.md`

本项目边界必须保持：

- MVP 原型。
- 使用模拟 ERP/MES/WMS 数据。
- Agent 工具全部只读。
- 不接真实企业生产系统。
- 不执行出库、调账、审批、下单等业务写操作。

当前云服务器已完成部署验证：

- 腾讯云轻量应用服务器
- IP：`43.136.25.67`
- Ubuntu 24.04 LTS
- Docker Compose 部署
- `docs/cloud-deployment-check-report.md` 已显示 `Status: Verified`

不要重新讨论买哪家服务器，除非我明确要求。

本次目标：专心优化产品不足，优先处理以下问题。

1. 权限中心

- 管理员直接更改角色/用户权限时必须填写备注。
- 如果没有用户申请单，来源默认记录为“管理员更改权限”。
- 后台需要新增权限变更留痕能力，例如 `permission_change_log`。
- 权限变动要记录：来源、操作者、目标用户或角色、权限项、变更前后值、备注、时间、关联申请单。
- 来源至少区分：
  - `request_approval`：申请审批
  - `admin_direct_change`：管理员更改
  - `system_seed`：系统初始化
- 权限矩阵按业务后台习惯设计：纵向菜单树，横向权限动作或权限名，最多三级菜单。
- 区分“当前角色已拥有”“对该角色可见”“普通用户可申请”。

2. 审批中心

- 审批不能只有通过/驳回，必须填写审批原因。
- 审批理由要落库并能在审计中追踪。
- 审批列表要展示申请说明、审批备注、状态、来源、申请人、审批时间。
- 支持 pending / approved / rejected / all 切换。
- 审批通过后提示用户刷新权限或重新登录后生效。

3. 审计与刷新体验

- 审计、运营看板、审批中心、部署状态等页面切换进入时自然刷新。
- 保留用户当前选择，不要刷新后让界面跳空。
- 工具日志和权限变动日志要支持详情面板。
- 有输入和编辑的页面统一做草稿暂存，防止网络失败、误点菜单、刷新导致重输。
- 提交成功后清理草稿。

4. 部署中心

- 明确它是“部署状态/运维只读控制台”，不是文件路径列表。
- 新增只读部署状态 API，展示容器状态、镜像、启动时间、最近健康检查。
- 新增只读日志 API，管理员能看 backend/nginx/postgres 最近 N 行日志。
- 页面解释哪些来自实时 API，哪些来自部署报告。

5. 业务问答体验

- 普通用户主界面不要展示英文内部码，例如 intent、risk、tool code、key-value 证据。
- 主反馈全部用中文业务语言；英文 code 只保留在折叠的审计/原始详情里。
- 增加历史会话侧边栏，类似 Codex/ChatGPT。
- 增加常见问题入口：订单发货、工单开工、采购延期、库存批次、异常 SOP。
- 支持继续追问，并复用上一轮实体上下文。

执行方式：

- 先检查当前代码和已有测试。
- 先处理权限变更留痕和审批理由落库，因为这是业务后台可信度核心。
- 改后运行相关后端测试、前端 smoke、前端 build。
- 如果有云端部署变更，再重新打包并部署到 `43.136.25.67`。
- 不要伪造生产级、真实企业接入、效率提升等说法。

注意：上一轮中途做过局部代码调整，包括 SOP 未命中中文化、发货风险证据中文化、审批意见 textarea、`business_identifier_not_found` 中文标签。下轮开始时请先检查这些改动并验证。
