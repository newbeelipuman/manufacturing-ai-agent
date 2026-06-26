import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import {
  Activity,
  ClipboardCheck,
  FileSearch,
  Gauge,
  History,
  LayoutDashboard,
  LockKeyhole,
  LogOut,
  MessageSquareText,
  MoreHorizontal,
  PanelLeftClose,
  PanelLeftOpen,
  Plus,
  Search,
  SendHorizontal,
  Server,
  ShieldCheck
} from "lucide-react";
import {
  askAgent,
  getAgentLogDetail,
  decidePermissionRequest,
  getAgentLogs,
  getAdminMetrics,
  getAdminPermissionRequests,
  getDeploymentLogs,
  getDeploymentReport,
  getDeploymentStatus,
  getAuthPermissions,
  getHealth,
  getMenus,
  getMyPermissionRequests,
  getPermissionChangeLogs,
  getToolLogs,
  getToolLogDetail,
  getUsageStats,
  login,
  saveRolePermissions,
  searchKnowledge,
  submitPermissionRequest
} from "./api";
import {
  demoPermissions,
  navItemsFromServerMenus,
  permissionCatalog,
  roleLabels,
  rolePermissionMatrix,
  visibleNavItems,
  type NavKey
} from "./permissions";
import type {
  AgentLog,
  AgentLogDetail,
  AdminMetrics,
  ChatResponse,
  DeploymentLogResponse,
  DeploymentReportResponse,
  DeploymentStatusResponse,
  KnowledgeResult,
  PermissionChangeLog,
  PermissionRequest,
  Role,
  SessionUser,
  ToolLog,
  ToolLogDetail,
  UsageStats
} from "./types";

const demoQuestions = [
  "订单 O1001 现在能不能发货？",
  "工单 WO1001 今天能不能开工，缺哪些物料？",
  "采购单 PO1001 延期会影响哪些客户订单？",
  "SKU-KB-001 当前可用库存是多少？有哪些批次？",
  "注塑件外观不良应该怎么处理？"
];

const iconByNav: Record<NavKey, ReactNode> = {
  chat: <MessageSquareText size={18} />,
  dashboard: <Gauge size={18} />,
  audit: <ClipboardCheck size={18} />,
  knowledge: <FileSearch size={18} />,
  permissions: <LockKeyhole size={18} />,
  approvals: <ShieldCheck size={18} />,
  deployment: <Server size={18} />
};

const roleOptions: Role[] = [
  "admin",
  "production_manager",
  "sales",
  "warehouse",
  "purchase",
  "normal_user"
];

function JsonBlock({ value }: { value: unknown }) {
  return <pre className="json-block">{JSON.stringify(value, null, 2)}</pre>;
}

const riskLabels: Record<string, string> = {
  high: "高风险",
  medium: "中风险",
  low: "低风险",
  unknown: "未识别"
};

const intentLabels: Record<string, string> = {
  order_delivery_risk: "订单发货风险分析",
  work_order_readiness: "工单开工齐套分析",
  purchase_delay_impact: "采购延期影响分析",
  inventory_batches: "库存批次查询",
  exception_sop: "异常 SOP 检索",
  clarify_order_delivery_risk: "需要补充订单号",
  clarify_work_order_readiness: "需要补充工单号",
  clarify_purchase_delay_impact: "需要补充采购单号",
  clarify_inventory_batches: "需要补充 SKU 编码"
};

const reasonLabels: Record<string, string> = {
  inventory_shortage: "库存缺口",
  quality_hold: "质量冻结",
  purchase_delay: "采购延期",
  work_order_replenishment: "工单补货",
  work_order_material_shortage: "工单缺料",
  business_identifier_not_found: "未识别到业务编号",
  permission_denied: "权限不足",
  clarification_required: "需要补充信息"
};

const toolLabels: Record<string, string> = {
  query_order_status: "查询销售订单",
  query_inventory_by_sku: "查询 SKU 库存",
  query_work_order: "查询工单",
  query_purchase_arrival: "查询采购到货",
  query_exception_sop: "查询异常 SOP",
  analyze_order_delivery_risk: "分析订单交付风险",
  analyze_work_order_readiness: "分析工单开工齐套",
  analyze_purchase_delay_impact: "分析采购延期影响"
};

function labelCode(code: string) {
  return reasonLabels[code] ?? code;
}

function TagList({ items }: { items: string[] }) {
  if (!items.length) {
    return <p className="empty compact">暂无</p>;
  }
  return (
    <div className="tag-list">
      {items.map((item) => (
        <span key={item}>{labelCode(item)}</span>
      ))}
    </div>
  );
}

function ToolPermissionTable({ tools }: { tools: ChatResponse["called_tools"] }) {
  return (
    <div className="tool-table">
      {tools.map((tool) => (
        <div className="tool-row" key={tool.tool_name}>
          <strong>{toolLabels[tool.tool_name] ?? tool.tool_name}</strong>
          <span className={tool.permission_allowed ? "ok" : "deny"}>
            {tool.permission_allowed ? "已授权" : "已拒绝"}
          </span>
          <span>{tool.success ? "成功" : "失败"}</span>
        </div>
      ))}
    </div>
  );
}

function LoginPage({
  onLogin,
  sessionMessage
}: {
  onLogin: (user: SessionUser) => void;
  sessionMessage?: string;
}) {
  const [username, setUsername] = useState("demo_admin");
  const [role, setRole] = useState<Role>("admin");
  const [password, setPassword] = useState("demo123456");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setError("");
    try {
      const response = await login({ username, password });
      const [menusResponse, permissionsResponse] = await Promise.all([
        getMenus(response.access_token),
        getAuthPermissions(response.access_token)
      ]);
      onLogin({
        username: response.user.username,
        role: response.user.role,
        token: response.access_token,
        displayName: response.user.display_name,
        menus: menusResponse.menus,
        permissions: permissionsResponse.permissions
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-panel">
        <p className="eyebrow">Manufacturing AI Agent</p>
        <h1>企业 AI Agent 控制台</h1>
        <p className="muted">
          使用 demo 账号登录后获取 JWT；服务端 RBAC 会重新校验菜单、API、文档和工具权限。
        </p>
        <label>
          用户名
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          角色
          <select value={role} onChange={(event) => setRole(event.target.value as Role)}>
            {roleOptions.map((item) => (
              <option key={item} value={item}>
                {roleLabels[item]}
              </option>
            ))}
          </select>
        </label>
        <label>
          密码
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />
        </label>
        {sessionMessage ? <p className="error">{sessionMessage}</p> : null}
        {error ? <p className="error">{error}</p> : null}
        <button className="primary" onClick={submit} disabled={loading}>
          {loading ? "登录中..." : "进入控制台"}
        </button>
        <p className="boundary">
          MVP 使用模拟 ERP/MES/WMS 数据；Agent 工具只读，不执行出库、调账、审批、下单等业务写操作。
        </p>
      </section>
    </main>
  );
}

function ChatWorkbench({ user }: { user: SessionUser }) {
  const [question, setQuestion] = useState(demoQuestions[0]);
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [assistantOpen, setAssistantOpen] = useState(true);
  const [historySearch, setHistorySearch] = useState("");
  const [history, setHistory] = useState<Array<{ question: string; conclusion: string }>>(() => {
    try {
      return JSON.parse(window.localStorage.getItem("chat-history-draft") ?? "[]");
    } catch {
      return [];
    }
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit() {
    setLoading(true);
    setError("");
    try {
      const nextResponse = await askAgent({ ...user, question, token: user.token });
      setResponse(nextResponse);
      const nextHistory = [
        {
          question,
          conclusion: nextResponse.business_conclusion || nextResponse.answer
        },
        ...history.filter((item) => item.question !== question)
      ].slice(0, 20);
      setHistory(nextHistory);
      window.localStorage.setItem("chat-history-draft", JSON.stringify(nextHistory));
    } catch (err) {
      setError(err instanceof Error ? err.message : "请求失败");
    } finally {
      setLoading(false);
    }
  }

  const responseTitle = response?.success === false ? "需要补充信息" : "分析结果";
  const filteredHistory = history.filter((item) => {
    const keyword = historySearch.trim().toLowerCase();
    if (!keyword) {
      return true;
    }
    return `${item.question} ${item.conclusion}`.toLowerCase().includes(keyword);
  });

  return (
    <section className={`chat-shell codex-chat-shell ${assistantOpen ? "" : "assistant-collapsed"}`}>
      <aside className="chat-assistant-rail codex-thread-rail" aria-label="问答辅助栏">
        <button
          className="icon-button rail-toggle"
          title={assistantOpen ? "收起辅助栏" : "展开辅助栏"}
          aria-label={assistantOpen ? "收起辅助栏" : "展开辅助栏"}
          onClick={() => setAssistantOpen((open) => !open)}
        >
          {assistantOpen ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
        </button>
        {assistantOpen ? (
          <div className="chat-assistant-inner">
            <section className="rail-section">
              <div className="rail-heading">
                <MessageSquareText size={16} />
                <h3>常见问题</h3>
              </div>
              <div className="question-shortcuts">
                {demoQuestions.map((item) => (
                  <button key={item} onClick={() => setQuestion(item)}>
                    {item}
                  </button>
                ))}
              </div>
            </section>
            <section className="rail-section rail-section-fill">
              <div className="rail-heading">
                <History size={16} />
                <h3>历史聊天</h3>
              </div>
              <label className="search-field" aria-label="搜索历史聊天">
                <Search size={15} />
                <input
                  value={historySearch}
                  onChange={(event) => setHistorySearch(event.target.value)}
                  placeholder="搜索历史"
                />
              </label>
              {filteredHistory.length ? (
                <div className="history-list">
                  {filteredHistory.map((item) => (
                    <button
                      className="history-row"
                      key={item.question}
                      onClick={() => setQuestion(item.question)}
                    >
                      <strong>{item.question}</strong>
                      <span>{item.conclusion}</span>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="empty compact">暂无匹配历史。</p>
              )}
            </section>
          </div>
        ) : null}
      </aside>

      <div className="chat-conversation">
        <header className="chat-conversation-header">
          <div>
            <h2>{question}</h2>
            <p className="muted compact">业务问答 / 单条问题分析模式</p>
          </div>
          <div className="chat-header-actions">
            <span className="pill">{user.role}</span>
            <button className="icon-button" title="更多" aria-label="更多">
              <MoreHorizontal size={18} />
            </button>
          </div>
        </header>
        {error ? <p className="error">{error}</p> : null}

        <div className="chat-message-scroll">
          <div className="followup-note codex-note">
            后续优化标记：有限次数追问会作为会话层能力单独设计；当前先保持单条问题边界，避免多问题文本污染 SOP 向量检索和审计记录。
          </div>
          {response ? (
            <div className="message-stack">
              <article className="chat-message user-message">
                <p>{question}</p>
              </article>
              <article className="chat-message assistant-message answer">
                <div className="assistant-message-title">
                  <h3>{responseTitle}</h3>
                  <span>{response.requires_human_review ? "需要人工复核" : "只读分析"}</span>
                </div>
                <div className="summary-grid">
                  <section>
                    <span className="section-label">业务结论</span>
                    <p>{response.business_conclusion}</p>
                  </section>
                  <section>
                    <span className="section-label">建议下一步</span>
                    <p>{response.suggested_next_action}</p>
                  </section>
                </div>
                <div className="metric-row">
                  <span>意图：{intentLabels[response.intent] ?? response.intent}</span>
                  <span>风险：{riskLabels[response.risk_level] ?? response.risk_level}</span>
                  <span>人工复核：{response.requires_human_review ? "需要" : "不需要"}</span>
                </div>
                <div className="result-sections">
                  <section>
                    <h4>检查数据</h4>
                    <TagList items={response.checked_data} />
                  </section>
                  <section>
                    <h4>风险因素</h4>
                    <TagList items={response.risk_factors} />
                  </section>
                  <section>
                    <h4>人工复核原因</h4>
                    <TagList items={response.manual_review_reason} />
                  </section>
                </div>
                <details className="raw-answer">
                  <summary>原始回答与审计文本</summary>
                  <p>{response.answer}</p>
                </details>
                <div className="answer-details-grid">
                  <section>
                    <h4>工具与权限</h4>
                    <ToolPermissionTable tools={response.called_tools} />
                  </section>
                  <section>
                    <h4>证据</h4>
                    <TagList items={response.evidence} />
                  </section>
                  <section>
                    <h4>建议</h4>
                    <TagList items={response.recommendations} />
                  </section>
                </div>
                <details className="raw-answer">
                  <summary>决策记录</summary>
                  <JsonBlock value={response.decision_record} />
                </details>
              </article>
            </div>
          ) : (
            <div className="chat-empty-state">
              <h2>制造业务只读问答</h2>
              <p>输入问题后会展示业务回答、工具调用、权限结果和决策记录。</p>
            </div>
          )}
        </div>

        <div className="chat-composer">
          <select
            className="composer-preset"
            aria-label="演示问题"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
          >
            {demoQuestions.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </select>
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="询问订单、工单、采购、库存或 SOP..."
          />
          <div className="composer-actions">
            <button className="icon-button" title="添加上下文" aria-label="添加上下文">
              <Plus size={18} />
            </button>
            <span className="composer-boundary">只读访问</span>
            <button className="primary send-button" onClick={submit} disabled={loading}>
              {loading ? "分析中..." : "开始分析"}
              <SendHorizontal size={16} />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}

function AdminDashboard({ user }: { user: SessionUser }) {
  const [stats, setStats] = useState<UsageStats | null>(null);
  const [metrics, setMetrics] = useState<AdminMetrics | null>(null);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [usageStats, operationalMetrics] = await Promise.all([
        getUsageStats(user.role, user.token),
        getAdminMetrics(user.role, user.token)
      ]);
      setStats(usageStats);
      setMetrics(operationalMetrics);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }

  useEffect(() => {
    void load();
  }, [user.token, user.role]);

  return (
    <section className="panel">
      <div className="panel-title">
        <h2>运营看板</h2>
        <button onClick={load}>刷新用量统计</button>
      </div>
      {error ? <p className="error">{error}</p> : null}
      {stats ? (
        <>
          <div className="stats-grid">
            <div><strong>{stats.total_agent_calls}</strong><span>Agent calls</span></div>
            <div><strong>{stats.total_tool_calls}</strong><span>Tool calls</span></div>
            <div><strong>{(stats.success_rate * 100).toFixed(1)}%</strong><span>Success rate</span></div>
            <div><strong>{(stats.denied_rate * 100).toFixed(1)}%</strong><span>Denied rate</span></div>
            <div><strong>{stats.avg_latency_ms}</strong><span>Avg latency ms</span></div>
          </div>
          {metrics ? (
            <>
              <h3>运行指标</h3>
              <div className="stats-grid">
                <div><strong>{metrics.total_requests}</strong><span>总请求数</span></div>
                <div><strong>{metrics.total_agent_calls}</strong><span>Metric agent calls</span></div>
                <div><strong>{metrics.total_tool_calls}</strong><span>Metric tool calls</span></div>
                <div><strong>{metrics.high_risk_count}</strong><span>高风险次数</span></div>
                <div><strong>{metrics.avg_latency_ms}</strong><span>Metric avg latency</span></div>
              </div>
            </>
          ) : null}
          <div className="two-col">
            <div>
              <h3>高频工具</h3>
              <JsonBlock value={stats.top_tools} />
            </div>
            <div>
              <h3>高频意图</h3>
              <JsonBlock value={stats.top_intents} />
            </div>
          </div>
        </>
      ) : (
        <p className="empty">点击刷新读取 `/api/admin/usage-stats`。</p>
      )}
    </section>
  );
}

type AuditFilters = {
  requestId: string;
  username: string;
  logRole: string;
  intent: string;
  toolName: string;
  permissionAllowed: "" | "true" | "false";
  changeSource: string;
  targetIdentifier: string;
};

const emptyAuditFilters: AuditFilters = {
  requestId: "",
  username: "",
  logRole: "",
  intent: "",
  toolName: "",
  permissionAllowed: "",
  changeSource: "",
  targetIdentifier: ""
};

function AuditLogs({ user }: { user: SessionUser }) {
  const [agentLogs, setAgentLogs] = useState<AgentLog[]>([]);
  const [toolLogs, setToolLogs] = useState<ToolLog[]>([]);
  const [permissionChanges, setPermissionChanges] = useState<PermissionChangeLog[]>([]);
  const [filters, setFilters] = useState<AuditFilters>(emptyAuditFilters);
  const [selected, setSelected] = useState<
    AgentLog | AgentLogDetail | ToolLog | ToolLogDetail | PermissionChangeLog | null
  >(null);
  const [error, setError] = useState("");
  const [detailLoading, setDetailLoading] = useState(false);

  async function load(nextFilters = filters) {
    setError("");
    try {
      const [agents, tools, changes] = await Promise.all([
        getAgentLogs(user.role, user.token, {
          request_id: nextFilters.requestId.trim(),
          username: nextFilters.username.trim(),
          log_role: nextFilters.logRole,
          intent: nextFilters.intent.trim()
        }),
        getToolLogs(user.role, user.token, {
          request_id: nextFilters.requestId.trim(),
          username: nextFilters.username.trim(),
          log_role: nextFilters.logRole,
          tool_name: nextFilters.toolName.trim(),
          permission_allowed:
            nextFilters.permissionAllowed === "" ? "" : nextFilters.permissionAllowed === "true"
        }),
        getPermissionChangeLogs({
          token: user.token,
          source: nextFilters.changeSource,
          operator_username: nextFilters.username.trim(),
          target_identifier: nextFilters.targetIdentifier.trim()
        })
      ]);
      setAgentLogs(agents.data);
      setToolLogs(tools.data);
      setPermissionChanges(changes.data ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    }
  }

  async function selectAgentLog(log: AgentLog) {
    setSelected(log);
    setDetailLoading(true);
    setError("");
    try {
      setSelected(await getAgentLogDetail(user.role, log.id, user.token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载调用详情失败");
    } finally {
      setDetailLoading(false);
    }
  }

  async function selectToolLog(log: ToolLog) {
    setSelected(log);
    setDetailLoading(true);
    setError("");
    try {
      setSelected(await getToolLogDetail(user.role, log.id, user.token));
    } catch (err) {
      setError(err instanceof Error ? err.message : "工具日志详情加载失败");
    } finally {
      setDetailLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, [user.token, user.role]);

  function resetFilters() {
    setFilters(emptyAuditFilters);
    void load(emptyAuditFilters);
  }

  return (
    <section className="workspace-grid">
      <div className="panel span-12">
        <div className="panel-title">
          <h2>审计筛选</h2>
          <div className="toolbar-actions">
            <button onClick={() => load()}>应用筛选</button>
            <button onClick={resetFilters}>清空</button>
          </div>
        </div>
        <div className="filter-grid">
          <label>
            请求 ID
            <input
              value={filters.requestId}
              onChange={(event) => setFilters({ ...filters, requestId: event.target.value })}
              placeholder="x-request-id"
            />
          </label>
          <label>
            用户名
            <input
              value={filters.username}
              onChange={(event) => setFilters({ ...filters, username: event.target.value })}
              placeholder="demo_admin"
            />
          </label>
          <label>
            角色
            <select
              value={filters.logRole}
              onChange={(event) => setFilters({ ...filters, logRole: event.target.value })}
            >
              <option value="">全部角色</option>
              {roleOptions.map((item) => (
                <option key={item} value={item}>
                  {roleLabels[item]}
                </option>
              ))}
            </select>
          </label>
          <label>
            意图
            <input
              value={filters.intent}
              onChange={(event) => setFilters({ ...filters, intent: event.target.value })}
              placeholder="order_delivery_risk"
            />
          </label>
          <label>
            工具
            <input
              value={filters.toolName}
              onChange={(event) => setFilters({ ...filters, toolName: event.target.value })}
              placeholder="query_order_status"
            />
          </label>
          <label>
            工具权限
            <select
              value={filters.permissionAllowed}
              onChange={(event) =>
                setFilters({
                  ...filters,
                  permissionAllowed: event.target.value as AuditFilters["permissionAllowed"]
                })
              }
            >
              <option value="">全部</option>
              <option value="true">已放行</option>
              <option value="false">已拒绝</option>
            </select>
          </label>
          <label>
            权限变更来源
            <select
              value={filters.changeSource}
              onChange={(event) => setFilters({ ...filters, changeSource: event.target.value })}
            >
              <option value="">全部来源</option>
              <option value="request_approval">申请审批</option>
              <option value="admin_direct_change">管理员直接变更</option>
            </select>
          </label>
          <label>
            变更对象
            <input
              value={filters.targetIdentifier}
              onChange={(event) =>
                setFilters({ ...filters, targetIdentifier: event.target.value })
              }
              placeholder="demo_user / sales"
            />
          </label>
        </div>
      </div>
      <div className="panel span-4">
        <div className="panel-title">
          <h2>Agent 调用日志</h2>
          <button onClick={() => load()}>刷新</button>
        </div>
        {error ? <p className="error">{error}</p> : null}
        {agentLogs.map((log) => (
          <button className="log-row" key={`agent-${log.id}`} onClick={() => selectAgentLog(log)}>
            <span>#{log.id}</span>
            <span>{log.intent || log.question}</span>
            <span>{String(log.success)}</span>
          </button>
        ))}
      </div>
      <div className="panel span-4">
        <h2>工具调用日志</h2>
        {toolLogs.map((log) => (
          <button className="log-row" key={`tool-${log.id}`} onClick={() => selectToolLog(log)}>
            <span>#{log.id}</span>
            <span>{toolLabels[log.tool_name] ?? log.tool_name}</span>
            <span className={log.permission_allowed ? "ok" : "deny"}>
              {log.permission_allowed ? "已放行" : "已拒绝"}
            </span>
          </button>
        ))}
      </div>
      <div className="panel span-4">
        <h2>权限变更留痕</h2>
        {permissionChanges.map((log) => (
          <button className="log-row" key={`permission-${log.id}`} onClick={() => setSelected(log)}>
            <span>#{log.id}</span>
            <span>{log.source}</span>
            <span>{log.target_identifier}</span>
          </button>
        ))}
      </div>
      <div className="panel span-12">
        <h2>调用详情</h2>
        {detailLoading ? (
          <p className="empty">加载调用详情...</p>
        ) : selected ? (
          <JsonBlock value={selected} />
        ) : (
          <p className="empty">选择一条日志查看详情。</p>
        )}
      </div>
    </section>
  );
}

function KnowledgeSearch({ user }: { user: SessionUser }) {
  const [query, setQuery] = useState("注塑件外观不良应该怎么处理？");
  const [results, setResults] = useState<KnowledgeResult[]>([]);
  const [error, setError] = useState("");

  async function submit() {
    setError("");
    try {
      const response = await searchKnowledge({ role: user.role, query, token: user.token });
      if (!response.permission_allowed) {
        setError(response.message);
        setResults([]);
        return;
      }
      setResults(response.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "检索失败");
    }
  }

  return (
    <section className="panel">
      <div className="panel-title">
        <h2>知识库检索</h2>
        <button onClick={submit}>检索 SOP</button>
      </div>
      <input value={query} onChange={(event) => setQuery(event.target.value)} />
      {error ? <p className="error">{error}</p> : null}
      <div className="result-list">
        {results.map((item) => (
          <article className="result-row" key={`${item.source_path}-${item.score}`}>
            <h3>{item.doc_title}</h3>
            <p>{item.chunk_text}</p>
            <div className="metric-row">
              <span>{item.source_path}</span>
              <span>score: {item.score}</span>
              <span>matched: {item.matched_terms.join(", ")}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

function PermissionCenter({
  user,
  onRefreshAccess
}: {
  user: SessionUser;
  onRefreshAccess: () => void;
}) {
  const [requests, setRequests] = useState<PermissionRequest[]>([]);
  const [permission, setPermission] = useState("menu:admin-dashboard");
  const [reason, setReason] = useState("需要查看 usage dashboard 以排查演示调用情况。");
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const response = await getMyPermissionRequests(user.token);
      setRequests(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载申请历史失败");
    }
  }

  async function submit() {
    setError("");
    try {
      const response = await submitPermissionRequest({
        token: user.token,
        requested_permission: permission,
        reason
      });
      setRequests((items) => [response.data, ...items]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交申请失败");
    }
  }

  return (
    <section className="workspace-grid">
      <div className="panel span-6">
        <div className="panel-title">
          <h2>当前用户权限</h2>
          <button onClick={onRefreshAccess}>刷新 RBAC</button>
        </div>
        <ul className="permission-list">
          {(user.permissions?.length ? user.permissions : demoPermissions[user.role]).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
      <div className="panel span-6">
        <h2>申请权限</h2>
        <p className="muted">审批的是平台访问权限，不是订单、采购、出库等业务审批。</p>
        <label>
          申请项
          <input value={permission} onChange={(event) => setPermission(event.target.value)} />
        </label>
        <label>
          申请原因
          <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
        </label>
        <button onClick={submit}>提交权限申请</button>
        {error ? <p className="error">{error}</p> : null}
      </div>
      <div className="panel span-12">
        <div className="panel-title">
          <h2>申请历史</h2>
          <button onClick={load}>刷新</button>
        </div>
        {requests.length ? <JsonBlock value={requests} /> : <p className="empty">暂无申请记录。</p>}
      </div>
    </section>
  );
}

function PermissionCenterV2({
  user,
  onRefreshAccess
}: {
  user: SessionUser;
  onRefreshAccess: () => void;
}) {
  const [requests, setRequests] = useState<PermissionRequest[]>([]);
  const selectableRoles = user.role === "admin" ? roleOptions : [user.role];
  const [selectedRole, setSelectedRole] = useState<Role>(user.role);
  const [roleOverrides, setRoleOverrides] = useState<Partial<Record<Role, string[]>>>({});
  const [draftPermissions, setDraftPermissions] = useState<string[]>(
    rolePermissionMatrix[user.role]
  );
  const [isEditing, setIsEditing] = useState(false);
  const requestablePermissions = permissionCatalog.filter((item) => item.requestable);
  const [permission, setPermission] = useState(requestablePermissions[0]?.code ?? "");
  const [reason, setReason] = useState(
    () => window.localStorage.getItem("permission-request-reason-draft") ?? "需要临时查看运营数据，用于排查演示调用情况。"
  );
  const [adminChangeNote, setAdminChangeNote] = useState(
    () => window.localStorage.getItem("admin-permission-change-note-draft") ?? "管理员临时调整角色权限，用于演示或排查平台访问问题。"
  );
  const [draftSavedAt, setDraftSavedAt] = useState("");
  const [error, setError] = useState("");
  const activePermissionSet = new Set(
    selectedRole === user.role && user.permissions?.length
      ? user.permissions
      : roleOverrides[selectedRole]
        ? roleOverrides[selectedRole]
      : rolePermissionMatrix[selectedRole]
  );
  const visibleForSelectedRole = permissionCatalog.filter((item) =>
    activePermissionSet.has(item.code)
  );
  const requestableForUser = requestablePermissions.filter(
    (item) => !activePermissionSet.has(item.code) || user.role === "normal_user"
  );

  async function load() {
    setError("");
    try {
      const response = await getMyPermissionRequests(user.token);
      setRequests(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载申请历史失败");
    }
  }

  async function submit() {
    setError("");
    try {
      const response = await submitPermissionRequest({
        token: user.token,
        requested_permission: permission,
        reason
      });
      setRequests((items) => [response.data, ...items]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "提交申请失败");
    }
  }

  useEffect(() => {
    void load();
  }, [user.token]);

  useEffect(() => {
    window.localStorage.setItem("permission-request-reason-draft", reason);
  }, [reason]);

  useEffect(() => {
    window.localStorage.setItem("admin-permission-change-note-draft", adminChangeNote);
  }, [adminChangeNote]);

  useEffect(() => {
    function warnBeforeUnload(event: BeforeUnloadEvent) {
      if (!isEditing) {
        return;
      }
      event.preventDefault();
      event.returnValue = "";
    }
    window.addEventListener("beforeunload", warnBeforeUnload);
    return () => window.removeEventListener("beforeunload", warnBeforeUnload);
  }, [isEditing]);

  function changeRole(nextRole: Role) {
    setSelectedRole(nextRole);
    setDraftPermissions(roleOverrides[nextRole] ?? rolePermissionMatrix[nextRole]);
    setIsEditing(false);
  }

  function toggleDraftPermission(code: string) {
    setDraftPermissions((items) =>
      items.includes(code) ? items.filter((item) => item !== code) : [...items, code]
    );
  }

  async function saveAdminChange() {
    setError("");
    if (!adminChangeNote.trim()) {
      setError("Permission change remark is required.");
      return;
    }
    try {
      const response = await saveRolePermissions({
        token: user.token,
        role_code: selectedRole,
        permission_codes: draftPermissions,
        remark: adminChangeNote
      });
      setRoleOverrides((items) => ({
        ...items,
        [selectedRole]: response.data.permissions
      }));
      setDraftPermissions(response.data.permissions);
      setIsEditing(false);
      window.localStorage.removeItem("admin-permission-change-draft");
      setDraftSavedAt(
        `Permission change saved. Source: ${response.data.source}, log #${response.data.change_log_id}.`
      );
      if (selectedRole === user.role) {
        await onRefreshAccess();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save permission change failed");
    }
  }

  function saveLocalDraft() {
    const snapshot = {
      role: selectedRole,
      permissions: draftPermissions,
      note: adminChangeNote,
      saved_at: new Date().toISOString(),
      source: "admin_direct_change_draft"
    };
    window.localStorage.setItem("admin-permission-change-draft", JSON.stringify(snapshot));
    setDraftSavedAt("草稿已暂存到本机浏览器，尚未写入后端权限表。");
  }

  return (
    <section className="workspace-grid">
      <div className="panel span-12">
        <div className="panel-title">
          <div>
            <h2>角色权限矩阵</h2>
            <p className="muted">
              按菜单树查看角色可见、可调用、可申请的权限。权限变动必须备注并留痕；当前页面的管理员编辑为草稿预览，正式直改需走后端审计接口。
            </p>
          </div>
          <div className="toolbar">
            <select
              value={selectedRole}
              onChange={(event) => changeRole(event.target.value as Role)}
              aria-label="选择角色"
            >
              {selectableRoles.map((role) => (
                <option key={role} value={role}>
                  {roleLabels[role]}
                </option>
              ))}
            </select>
            <button onClick={onRefreshAccess}>刷新权限</button>
            {user.role === "admin" ? (
              <button onClick={() => setIsEditing((value) => !value)}>
                {isEditing ? "退出编辑" : "编辑角色"}
              </button>
            ) : null}
          </div>
        </div>
        {isEditing ? (
          <div className="notice-block">
            <p>
              当前为管理员直接调整权限的草稿预览，尚未写入后端权限表。正式落库时必须记录来源
              <strong> 管理员更改 </strong>、操作人、角色、权限差异、备注和时间。
            </p>
            <label>
              变更备注
              <textarea
                value={adminChangeNote}
                onChange={(event) => setAdminChangeNote(event.target.value)}
              />
            </label>
            <button onClick={saveLocalDraft}>暂存草稿</button>
            <button className="primary" onClick={saveAdminChange} disabled={!adminChangeNote.trim()}>
              Save to backend
            </button>
            {draftSavedAt ? <p className="muted">{draftSavedAt}</p> : null}
          </div>
        ) : null}
        <div className="permission-table-wrap">
          <table className="permission-table">
            <thead>
              <tr>
                <th>一级菜单</th>
                <th>二级/三级菜单</th>
                  <th>权限名</th>
                  <th>类型</th>
                  <th>当前角色</th>
                  <th>可申请</th>
                  <th>变更来源</th>
                </tr>
            </thead>
            <tbody>
              {permissionCatalog.map((item) => {
                const enabled = isEditing
                  ? draftPermissions.includes(item.code)
                  : activePermissionSet.has(item.code);
                return (
                  <tr key={item.code}>
                    <td>{item.menuPath[0]}</td>
                    <td>{item.menuPath.slice(1).join(" / ")}</td>
                    <td>
                      <strong>{item.name}</strong>
                      <span>{item.code}</span>
                    </td>
                    <td>{item.group.toUpperCase()}</td>
                    <td>
                      {isEditing ? (
                        <label className="inline-check">
                          <input
                            type="checkbox"
                            checked={enabled}
                            onChange={() => toggleDraftPermission(item.code)}
                          />
                          {enabled ? "已授予" : "未授予"}
                        </label>
                      ) : (
                        <span className={enabled ? "ok" : "muted"}>
                          {enabled ? "已授予" : "未授予"}
                        </span>
                      )}
                    </td>
                    <td>{item.requestable ? "允许" : "不开放"}</td>
                    <td>{isEditing ? "管理员更改草稿" : "角色基线/授权结果"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
      <div className="panel span-5">
        <div className="panel-title">
          <h2>当前账号权限</h2>
          <span className="pill">{roleLabels[user.role]}</span>
        </div>
        <div className="permission-chip-list">
          {visibleForSelectedRole.map((item) => (
            <span className="permission-chip" key={item.code}>
              {item.name}
            </span>
          ))}
        </div>
      </div>
      <div className="panel span-7">
        <h2>权限申请</h2>
        <p className="muted">
          申请的是平台访问权限，不是订单、采购、出库等业务审批。申请原因会进入审批记录和审计日志。
        </p>
        <label>
          申请项
          <select value={permission} onChange={(event) => setPermission(event.target.value)}>
            {requestableForUser.map((item) => (
              <option key={item.code} value={item.code}>
                {item.name}（{item.code}）
              </option>
            ))}
          </select>
        </label>
        <label>
          申请原因
          <textarea value={reason} onChange={(event) => setReason(event.target.value)} />
        </label>
        <button onClick={submit} disabled={!reason.trim()}>
          提交权限申请
        </button>
        {error ? <p className="error">{error}</p> : null}
      </div>
      <div className="panel span-12">
        <div className="panel-title">
          <h2>申请历史</h2>
          <button onClick={load}>刷新</button>
        </div>
        {requests.length ? (
          <div className="request-table-wrap">
            <table className="permission-table">
              <thead>
                <tr>
                  <th>申请人</th>
                  <th>权限项</th>
                  <th>状态</th>
                  <th>来源</th>
                  <th>审批人</th>
                  <th>原因</th>
                </tr>
              </thead>
              <tbody>
                {requests.map((item) => (
                  <tr key={item.id}>
                    <td>{item.requester_username}</td>
                    <td>{item.requested_permission}</td>
                    <td>{item.status}</td>
                    <td>申请审批</td>
                    <td>{item.approver_username || "-"}</td>
                    <td>{item.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="empty">暂无申请记录。</p>
        )}
      </div>
    </section>
  );
}

function AdminApprovalCenter({ user }: { user: SessionUser }) {
  const [requests, setRequests] = useState<PermissionRequest[]>([]);
  const [statusFilter, setStatusFilter] = useState<"pending" | "approved" | "rejected" | "all">("pending");
  const statusLabels: Record<typeof statusFilter, string> = {
    pending: "待审批",
    approved: "已通过",
    rejected: "已驳回",
    all: "全部"
  };
  const [comment, setComment] = useState(
    () => window.localStorage.getItem("approval-comment-draft") ?? "仅授予平台菜单访问权限，原因已核实。"
  );
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const response = await getAdminPermissionRequests({
        token: user.token,
        status: statusFilter
      });
      setRequests(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载待审批申请失败");
    }
  }

  async function decide(requestId: number, decision: "approve" | "reject") {
    setError("");
    if (!comment.trim()) {
      setError("审批意见必填，权限变动必须留痕。");
      return;
    }
    try {
      await decidePermissionRequest({
        token: user.token,
        requestId,
        decision,
        approval_comment: comment
      });
      setComment("");
      window.localStorage.removeItem("approval-comment-draft");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "审批失败");
    }
  }

  useEffect(() => {
    void load();
  }, [user.token, statusFilter]);

  useEffect(() => {
    if (comment.trim()) {
      window.localStorage.setItem("approval-comment-draft", comment);
    } else {
      window.localStorage.removeItem("approval-comment-draft");
    }
  }, [comment]);

  return (
    <section className="panel">
      <div className="panel-title">
        <h2>审批中心</h2>
        <button onClick={load}>刷新待审批</button>
      </div>
      <p className="muted">
        这里只审批平台访问权限。通过/驳回都会写入权限申请记录，并在工具调用日志中记录来源为申请审批。
      </p>
      <label>
        申请状态
        <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value as typeof statusFilter)}>
          <option value="pending">待审批</option>
          <option value="approved">已通过</option>
          <option value="rejected">已驳回</option>
          <option value="all">全部</option>
        </select>
      </label>
      <label className="approval-comment-label">
        审批意见
        <textarea
          className="approval-comment-box"
          value={comment}
          onChange={(event) => setComment(event.target.value)}
          placeholder="说明通过或驳回的原因，例如：仅授予平台菜单访问权限，申请原因与岗位职责一致。"
        />
        <span className="field-help">通过或驳回都会保存这段意见，用于权限变动留痕。</span>
      </label>
      {error ? <p className="error">{error}</p> : null}
      {requests.length ? (
        <div className="result-list">
          {requests.map((item) => (
            <article className="result-row" key={item.id}>
              <h3>{item.requester_username}</h3>
              <div className="metric-row">
                <span>权限项：{item.requested_permission}</span>
                <span>来源：申请审批</span>
                <span>状态：{statusLabels[item.status]}</span>
              </div>
              <p className="muted">申请说明：{item.reason}</p>
              <div className="metric-row">
                <button onClick={() => decide(item.id, "approve")} disabled={!comment.trim()}>
                  通过
                </button>
                <button onClick={() => decide(item.id, "reject")} disabled={!comment.trim()}>
                  驳回
                </button>
              </div>
            </article>
          ))}
        </div>
      ) : (
        <p className="empty">暂无{statusLabels[statusFilter]}权限申请。</p>
      )}
    </section>
  );
}

function DeploymentStatus() {
  const [health, setHealth] = useState("");
  const [error, setError] = useState("");

  async function check() {
    setError("");
    try {
      const response = await getHealth();
      setHealth(response.status);
    } catch (err) {
      setError(err instanceof Error ? err.message : "健康检查失败");
    }
  }

  useEffect(() => {
    void check();
  }, []);

  return (
    <section className="panel">
      <div className="panel-title">
        <h2>部署状态</h2>
        <button onClick={check}>检查 /health</button>
      </div>
      <p className="muted">
        部署状态用于演示环境健康检查、报告路径和运维证据说明；它不是文件浏览器。容器日志需要新增只读日志 API 后才能在页面内查看。
      </p>
      {health ? <p className="ok">health: {health}</p> : null}
      {error ? <p className="error">{error}</p> : null}
      <div className="two-col">
        <div>
          <h3>部署报告</h3>
          <p className="muted">云部署报告：docs/cloud-deployment-check-report.md</p>
          <p className="muted">演示报告：docs/demo-report.md</p>
        </div>
        <div>
          <h3>日志查看</h3>
          <p className="muted">当前版本请通过服务器命令查看容器日志：</p>
          <pre className="json-block">sudo docker compose -f docker-compose.yml -f docker-compose.cloud.yml --env-file .env.production logs --tail=120 backend</pre>
        </div>
      </div>
    </section>
  );
}

type DeploymentSubView = "logs" | "services" | "reports";

function DeploymentStatusV2({
  user,
  activeView,
  onViewChange
}: {
  user: SessionUser;
  activeView: DeploymentSubView;
  onViewChange: (view: DeploymentSubView) => void;
}) {
  const [health, setHealth] = useState("");
  const [status, setStatus] = useState<DeploymentStatusResponse | null>(null);
  const [selectedService, setSelectedService] = useState("backend");
  const [serviceLog, setServiceLog] = useState<DeploymentLogResponse | null>(null);
  const [selectedReport, setSelectedReport] = useState<DeploymentReportResponse | null>(null);
  const [reportLoadingId, setReportLoadingId] = useState("");
  const [reportQuery, setReportQuery] = useState("");
  const [error, setError] = useState("");

  async function check() {
    setError("");
    try {
      const [healthResponse, statusResponse] = await Promise.all([
        getHealth(),
        getDeploymentStatus(user.token)
      ]);
      setHealth(healthResponse.status);
      setStatus(statusResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deployment status load failed");
    }
  }

  async function loadLogs(service = selectedService) {
    setError("");
    try {
      setSelectedService(service);
      setServiceLog(await getDeploymentLogs({ token: user.token, service, tail: 120 }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Deployment log load failed");
    }
  }

  async function loadReport(reportId: string) {
    setError("");
    setReportLoadingId(reportId);
    try {
      setSelectedReport(await getDeploymentReport({ token: user.token, reportId }));
    } catch (err) {
      setError(err instanceof Error ? err.message : "部署报告加载失败");
    } finally {
      setReportLoadingId("");
    }
  }

  useEffect(() => {
    void check();
    void loadLogs("backend");
  }, [user.token]);

  const serviceLabels: Record<string, string> = {
    backend: "后端服务",
    nginx: "网关服务",
    postgres: "数据库",
    redis: "缓存服务"
  };
  const statusSourceLabels: Record<string, string> = {
    docker_compose: "Docker Compose",
    docker_compose_logs: "Docker Compose 日志",
    runtime_fallback: "运行时回退"
  };
  const stateLabels: Record<string, string> = {
    running: "运行中",
    exited: "已退出",
    paused: "已暂停",
    restarting: "重启中",
    dead: "异常",
    created: "已创建",
    unknown: "未知"
  };
  const reportLabelMap: Record<string, string> = {
    "cloud deployment report": "云部署验证报告",
    "demo report": "演示报告"
  };
  const reportIdByPath: Record<string, string> = {
    "docs/cloud-deployment-check-report.md": "cloud-deployment-check-report",
    "docs/demo-report.md": "demo-report"
  };
  const serviceOptions = ["backend", "nginx", "postgres", "redis"];
  const selectedServiceLabel = serviceLabels[selectedService] ?? selectedService;
  const reportFiles = status?.report_files ?? [
    {
      id: "cloud-deployment-check-report",
      label: "cloud deployment report",
      path: "docs/cloud-deployment-check-report.md",
      exists: true
    },
    { id: "demo-report", label: "demo report", path: "docs/demo-report.md", exists: true }
  ];
  const reportContent = selectedReport?.content ?? "";
  const reportQueryText = reportQuery.trim().toLowerCase();
  const reportMatches = reportQueryText
    ? reportContent
        .split("\n")
        .map((line, index) => ({ line, lineNumber: index + 1 }))
        .filter((item) => item.line.toLowerCase().includes(reportQueryText))
        .slice(0, 12)
    : [];

  function jumpToReportLine(lineNumber: number) {
    const target = document.getElementById(`report-line-${lineNumber}`);
    target?.scrollIntoView({ block: "center" });
  }

  return (
    <section className="deployment-shell">
      {error ? <p className="error">{error}</p> : null}

      {activeView === "logs" ? (
      <div className="deployment-section deployment-log-section">
        <div className="section-heading">
          <h3>日志查看</h3>
          <span>高频查看区域，只保留日志切换和原文窗口</span>
        </div>
        <div className="service-tabs" aria-label="日志服务">
          {serviceOptions.map((service) => (
            <button
              key={service}
              className={selectedService === service ? "active" : ""}
              onClick={() => loadLogs(service)}
            >
              {serviceLabels[service] ?? service}
            </button>
          ))}
        </div>
        {serviceLog ? (
          <>
            <p className="deployment-log-meta">
              {selectedServiceLabel}日志，来源：{statusSourceLabels[serviceLog.source] ?? serviceLog.source}。
              {serviceLog.message}
            </p>
            <pre className="json-block deployment-log">
              {serviceLog.lines.length ? serviceLog.lines.join("\n") : serviceLog.readonly_command}
            </pre>
          </>
        ) : (
          <pre className="json-block deployment-log">docker compose logs --tail=120 backend</pre>
        )}
      </div>
      ) : null}

      {activeView === "services" ? (
      <div className="deployment-section">
        <div className="deployment-hero compact-hero">
          <div>
            <h2>部署状态 / 只读运维控制台</h2>
            <p>
              实时读取健康检查、容器状态和最近日志；这里只做只读展示，不执行启动、停止、重启或部署操作。
            </p>
          </div>
          <button className="primary" onClick={check}>检查健康状态</button>
        </div>
        {status ? (
          <>
            <div className="deployment-summary">
              <div>
                <span>健康检查</span>
                <strong className={health === "ok" ? "ok" : "deny"}>{health || "未读取"}</strong>
              </div>
              <div>
                <span>运行环境</span>
                <strong>{status.environment}</strong>
              </div>
              <div>
                <span>应用版本</span>
                <strong>{status.version}</strong>
              </div>
              <div>
                <span>状态来源</span>
                <strong>{statusSourceLabels[status.source] ?? status.source}</strong>
              </div>
              <div>
                <span>Docker 可读</span>
                <strong>{status.docker_available ? "可读取" : "不可读取"}</strong>
              </div>
            </div>
            {status.message ? <p className="deployment-note">{status.message}</p> : null}
          </>
        ) : null}
        <div className="section-heading service-section-heading">
          <h3>服务状态</h3>
          <span>中频查看，点击服务可切换到对应日志</span>
        </div>
        {status?.services.length ? (
          <div className="service-grid">
            {status.services.map((item) => {
              const state = item.state || "unknown";
              return (
                <button
                  className={`service-card ${selectedService === item.name ? "active" : ""}`}
                  key={item.name}
                  onClick={() => {
                    onViewChange("logs");
                    void loadLogs(item.name);
                  }}
                >
                  <span className="service-card-title">{serviceLabels[item.name] ?? item.name}</span>
                  <strong className={state === "running" ? "ok" : "deny"}>
                    {stateLabels[state] ?? state}
                  </strong>
                  <small>{item.name}</small>
                  <small>{item.image || "镜像信息不可用"}</small>
                </button>
              );
            })}
          </div>
        ) : (
          <p className="empty">当前运行环境无法直接读取 Docker Compose 状态，请查看下方只读命令提示。</p>
        )}
      </div>
      ) : null}

      {activeView === "reports" ? (
      <div className="deployment-section">
        {selectedReport ? (
          <div className="report-detail">
            <div className="report-detail-header">
              <button
                onClick={() => {
                  setSelectedReport(null);
                  setReportQuery("");
                }}
              >
                返回
              </button>
              <div>
                <h3>{reportLabelMap[selectedReport.label] ?? selectedReport.label}</h3>
                <span>{selectedReport.path}</span>
              </div>
              <label className="report-search" aria-label="报告内容搜索">
                <input
                  value={reportQuery}
                  onChange={(event) => setReportQuery(event.target.value)}
                  placeholder="搜索报告内容"
                />
              </label>
            </div>
            {reportQueryText ? (
              <div className="report-match-list">
                {reportMatches.length ? (
                  reportMatches.map((match) => (
                    <button key={match.lineNumber} onClick={() => jumpToReportLine(match.lineNumber)}>
                      <strong>L{match.lineNumber}</strong>
                      <span>{match.line}</span>
                    </button>
                  ))
                ) : (
                  <p className="empty compact">没有匹配内容。</p>
                )}
              </div>
            ) : null}
            <pre className="json-block report-content report-content-full">
              {reportContent.split("\n").map((line, index) => {
                const lineNumber = index + 1;
                return (
                  <span
                    id={`report-line-${lineNumber}`}
                    className={
                      reportQueryText && line.toLowerCase().includes(reportQueryText)
                        ? "report-line report-line-match"
                        : "report-line"
                    }
                    key={lineNumber}
                  >
                    {line || " "}
                    {"\n"}
                  </span>
                );
              })}
            </pre>
          </div>
        ) : (
        <>
          <div className="section-heading">
            <h3>部署报告</h3>
            <span>低频查看，点开后进入独立阅读容器</span>
          </div>
          {reportFiles.map((file) => {
            const reportId = file.id ?? reportIdByPath[file.path];
            return (
            <div className="report-row" key={file.path}>
              <div className="report-main">
                <div className="report-title-line">
                  <strong>{reportLabelMap[file.label] ?? file.label}</strong>
                  <span className={`report-status ${file.exists ? "ok" : "deny"}`}>
                    {file.exists ? "存在" : "缺失"}
                  </span>
                </div>
                <span>{file.path}</span>
              </div>
              <div className="report-actions">
                <button
                  onClick={() => reportId && loadReport(reportId)}
                  disabled={!file.exists || !reportId || reportLoadingId === reportId}
                >
                  {reportLoadingId === reportId ? "读取中" : "查看"}
                </button>
              </div>
            </div>
            );
          })}
          <p className="empty compact">点击“查看”后进入报告阅读页。</p>
        </>
        )}
        </div>
      ) : null}
    </section>
  );
}

function App() {
  const [user, setUser] = useState<SessionUser | null>(null);
  const [active, setActive] = useState<NavKey>("chat");
  const [deploymentSubView, setDeploymentSubView] = useState<DeploymentSubView>("services");
  const [accessError, setAccessError] = useState("");
  const [sessionMessage, setSessionMessage] = useState("");
  const visibleItems = useMemo(() => {
    if (user?.menus?.length) {
      return navItemsFromServerMenus(user.menus);
    }
    return visibleNavItems(user?.role ?? "normal_user");
  }, [user?.menus, user?.role]);
  const isKnownPath = ["/", "/index.html"].includes(window.location.pathname);

  useEffect(() => {
    function onAuthExpired(event: Event) {
      const message =
        event instanceof CustomEvent && typeof event.detail === "string"
          ? event.detail
          : "登录已过期或未登录，请重新登录。";
      setUser(null);
      setActive("chat");
      setAccessError("");
      setSessionMessage(message);
    }

    window.addEventListener("auth-expired", onAuthExpired);
    return () => window.removeEventListener("auth-expired", onAuthExpired);
  }, []);

  async function refreshAccessState() {
    if (!user?.token) {
      return;
    }
    setAccessError("");
    try {
      const [menusResponse, permissionsResponse] = await Promise.all([
        getMenus(user.token),
        getAuthPermissions(user.token)
      ]);
      setUser({
        ...user,
        menus: menusResponse.menus,
        permissions: permissionsResponse.permissions
      });
    } catch (err) {
      setAccessError(err instanceof Error ? err.message : "刷新权限失败");
    }
  }

  function handleLogin(nextUser: SessionUser) {
    setSessionMessage("");
    setUser(nextUser);
  }

  if (!isKnownPath) {
    return (
      <main className="login-shell">
        <section className="login-panel">
          <p className="eyebrow">404</p>
          <h1>页面不存在</h1>
          <p className="muted">请返回控制台首页继续使用。</p>
          <button className="primary" onClick={() => window.location.assign("/")}>
            返回首页
          </button>
        </section>
      </main>
    );
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} sessionMessage={sessionMessage} />;
  }

  const canViewActive = visibleItems.some((item) => item.key === active);
  const activeKey = canViewActive ? active : visibleItems[0]?.key;

  return (
    <main className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-head">
          <div className="brand">
            <LayoutDashboard size={22} />
            <span>AI Agent Console</span>
          </div>
        </div>
        <nav aria-label="主导航">
          {visibleItems.map((item) => (
            <div
              className={item.key === "deployment" ? "nav-group deployment-nav-group" : "nav-group"}
              key={item.key}
            >
              <button
                className={activeKey === item.key ? "active" : ""}
                onClick={() => {
                  setActive(item.key);
                  if (item.key === "deployment") {
                    setDeploymentSubView("services");
                  }
                }}
              >
                {iconByNav[item.key]}
                <span>{item.label}</span>
              </button>
              {item.key === "deployment" ? (
                <div className="subnav" aria-label="部署状态二级导航">
                  <button
                    className={activeKey === "deployment" && deploymentSubView === "logs" ? "active" : ""}
                    onClick={() => {
                      setActive("deployment");
                      setDeploymentSubView("logs");
                    }}
                  >
                    日志查看
                  </button>
                  <button
                    className={activeKey === "deployment" && deploymentSubView === "services" ? "active" : ""}
                    onClick={() => {
                      setActive("deployment");
                      setDeploymentSubView("services");
                    }}
                  >
                    服务状态
                  </button>
                  <button
                    className={activeKey === "deployment" && deploymentSubView === "reports" ? "active" : ""}
                    onClick={() => {
                      setActive("deployment");
                      setDeploymentSubView("reports");
                    }}
                  >
                    部署报告
                  </button>
                </div>
              ) : null}
            </div>
          ))}
        </nav>
      </aside>
      <section className={`content ${activeKey === "chat" ? "chat-content" : ""}`}>
        <header className="topbar">
          <div>
            <p className="eyebrow">只读业务边界</p>
            <h1>制造业企业 AI Agent 全栈控制台</h1>
          </div>
          <div className="user-box">
            <Activity size={16} />
            <span>{user.username}</span>
            <span className="pill">{user.role}</span>
            <button onClick={refreshAccessState}>刷新权限</button>
            <button title="退出" onClick={() => setUser(null)}>
              <LogOut size={16} />
            </button>
          </div>
        </header>
        {accessError ? <p className="error">{accessError}</p> : null}
        {!activeKey ? (
          <section className="panel">
            <h2>无可用页面</h2>
            <p className="error">服务端 RBAC 未返回任何可访问菜单，请联系管理员申请平台访问权限。</p>
          </section>
        ) : null}
        {activeKey === "chat" ? <ChatWorkbench user={user} /> : null}
        {activeKey === "dashboard" ? <AdminDashboard user={user} /> : null}
        {activeKey === "audit" ? <AuditLogs user={user} /> : null}
        {activeKey === "knowledge" ? <KnowledgeSearch user={user} /> : null}
        {activeKey === "permissions" ? (
          <PermissionCenterV2 user={user} onRefreshAccess={refreshAccessState} />
        ) : null}
        {activeKey === "approvals" ? <AdminApprovalCenter user={user} /> : null}
        {activeKey === "deployment" ? (
          <DeploymentStatusV2
            user={user}
            activeView={deploymentSubView}
            onViewChange={setDeploymentSubView}
          />
        ) : null}
      </section>
    </main>
  );
}

export default App;
