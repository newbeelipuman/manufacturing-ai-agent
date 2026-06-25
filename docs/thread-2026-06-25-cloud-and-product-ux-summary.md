# 2026-06-25 云部署与产品体验优化对话总结

本文记录 2026-06-25 这一轮长对话的关键历程，供后续线程快速接上。

## 起点

本轮从 P12 云部署开始。用户已经购买腾讯云服务器，并说明：

- 服务器 IP：`43.136.25.67`
- 用户：`ubuntu`
- Docker / Docker Compose 已安装
- registry mirror 已配置
- `sudo docker run hello-world` 已成功

目标是继续从上传和部署项目开始。

## 云部署过程

主要完成：

- 解决 SSH/SCP 密码登录问题。
- 确认 `ubuntu` 用户可登录。
- 在服务器上开启 SSH 密码认证并重启 ssh。
- 通过 `sudo passwd ubuntu` 重置 `ubuntu` 用户密码。
- 使用本地 PowerShell 执行上传部署脚本，而不是在服务器里执行 Windows 路径。
- 构建 Docker 服务并运行 Nginx、FastAPI、PostgreSQL、Redis。
- 解决 PostgreSQL 旧 volume 导致的 `agent_user` 密码认证失败。
- 拉回 `docs/cloud-deployment-check-report.md`。
- 验证 `http://43.136.25.67` 云端部署通过。

云端验证结果：

- `/health` 正常。
- React 控制台可访问。
- 登录正常。
- `/api/chat` 正常。
- 管理员 usage stats 和 metrics 正常。
- 报告状态为 `Verified`。

## DeepSeek 调试

完成：

- 增加 DeepSeek 配置入口。
- 指导服务器 `.env.production` 中配置 DeepSeek。
- 给出 curl 命令测试 DeepSeek API。

观察到：

- DeepSeek `/models` 测试曾返回 `401 invalid api key`。
- 后续用户更换或重启后，项目主链路验证通过，但 DeepSeek Key 是否真实可用仍应以服务器 curl 测试为准。

经验：

- API Key 只放服务器 `.env.production`。
- 不把 Key 写入前端、文档、GitHub 或聊天。
- 业务主链路验证通过，不等于 LLM 外部 API 一定通过。

## 前端与产品体验问题

用户多次指出：当前 UI 虽然能跑，但不像真实业务系统。

已记录的产品问题：

- UI 需要白色、简洁、专业，不要像临时 demo。
- 权限中心应像 Java 后台常见角色权限矩阵：纵向菜单树，横向权限项，最多三级菜单。
- 权限要区分角色当前已有、对角色可见、普通用户可申请。
- 管理员更改权限必须填写备注；无申请单时来源默认是“管理员更改权限”。
- 审批中心必须填写审批原因，不只是通过/驳回。
- 后台要记录权限变动来源：申请审批、管理员更改、系统初始化。
- 权限变动必须留痕，能查询操作者、对象、前后差异、备注、时间。
- 审计等页面切换进来要自然刷新。
- 有编辑内容的页面需要草稿暂存，避免网络失败、误点和刷新导致重输。
- 部署中心作用不清晰，不能只显示文件路径；管理员需要看到日志详情。
- 业务问答需要历史聊天侧边栏、常见问题、继续追问能力。
- 普通工人或没有英语水平的管理者看不懂英文 intent、risk、tool code、key-value 证据；主反馈必须中文业务化。

这些问题已持久化到：

- `docs/p15-product-hardening-backlog.md`
- `docs/cloud-server-first-deployment-experience.md`

## 本轮已做的局部代码调整

本轮中途曾做过一些小范围代码调整，但最后用户要求先停止功能开发、转为整理问题和交接。

已改动方向包括：

- 后端部分 SOP 未命中反馈改为中文。
- 后端发货风险证据从英文 key-value 改为中文业务句。
- 前端审批中心审批意见从单行输入改成多行 textarea。
- 前端增加 `business_identifier_not_found` 的中文标签兜底。

下个线程继续开发前，应先检查这些改动并运行测试，不要默认它们已经完整验证。

建议验证：

```powershell
cd G:\manufacturing-ai-agent
python -m compileall app scripts
python -m pytest tests\test_p10_permission_requests.py tests\test_p13_observability.py tests\test_nuobida_plan.py -q --basetemp G:\manufacturing-ai-agent\.pytest-workspace-tmp\p15-next -p no:cacheprovider
cd frontend
npm run test:smoke
npm run build
```

## 下轮工作重点

下轮不要再花时间选服务器或解释云部署基础流程，除非部署出现新错误。

优先做：

1. 后端权限变更审计表和接口。
2. 管理员直接改权限必须备注并落库。
3. 审批中心审批理由落库、详情展示、状态筛选。
4. 审计中心增加权限变动详情。
5. 部署中心增加只读日志/容器状态 API。
6. 业务问答中文化彻底清理，普通用户主界面不展示英文内部码。
7. 历史会话侧边栏和常见问题入口。

继续遵守项目边界：

- 只读工具。
- 模拟 ERP/MES/WMS 数据。
- 不接真实生产系统。
- 不做出库、调账、审批、下单等业务写操作。
