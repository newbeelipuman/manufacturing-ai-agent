import type {
  AdminListResponse,
  AdminMetrics,
  AgentLog,
  AgentLogDetail,
  ChatResponse,
  DeploymentLogResponse,
  DeploymentReportResponse,
  DeploymentStatusResponse,
  KnowledgeResult,
  ServerMenu,
  PermissionRequest,
  PermissionChangeLog,
  Role,
  ToolLog,
  ToolLogDetail,
  UsageStats
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export class ApiError extends Error {
  status: number;
  details?: unknown;

  constructor(message: string, status: number, details?: unknown) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.details = details;
  }
}

function formatValidationDetails(details: unknown): string {
  if (!Array.isArray(details)) {
    return "";
  }
  return details
    .map((item) => {
      if (!item || typeof item !== "object") {
        return "";
      }
      const detail = item as { loc?: unknown; msg?: unknown; type?: unknown };
      const loc = Array.isArray(detail.loc) ? detail.loc.join(".") : String(detail.loc ?? "");
      const msg = typeof detail.msg === "string" ? detail.msg : String(detail.type ?? "");
      return loc && msg ? `${loc}: ${msg}` : msg;
    })
    .filter(Boolean)
    .slice(0, 3)
    .join("；");
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {})
    }
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    let message =
      typeof data?.error?.message === "string"
        ? data.error.message
        : `Request failed with ${response.status}`;
    if (response.status === 401) {
      message = "登录已过期或未登录，请重新登录。";
      if (typeof window !== "undefined") {
        window.dispatchEvent(new CustomEvent("auth-expired", { detail: message }));
      }
    }
    if (response.status === 403) {
      message = "当前账号没有访问该功能的权限。";
    }
    if (response.status === 422) {
      const validationDetails = formatValidationDetails(data?.error?.details);
      if (validationDetails) {
        message = `${message} ${validationDetails}`;
      }
    }
    throw new ApiError(message, response.status, data?.error?.details);
  }
  return data as T;
}

function authHeaders(token?: string): HeadersInit {
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function setOptionalQuery(query: URLSearchParams, key: string, value?: string | boolean) {
  if (value !== undefined && value !== "") {
    query.set(key, String(value));
  }
}

export function login(params: {
  username: string;
  password: string;
}): Promise<{
  success: boolean;
  access_token: string;
  token_type: string;
  user: { username: string; display_name: string; role: Role };
}> {
  return requestJson("/api/auth/login", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export function askAgent(params: {
  username: string;
  role: Role;
  question: string;
  token?: string;
}): Promise<ChatResponse> {
  return requestJson<ChatResponse>("/api/chat", {
    method: "POST",
    headers: authHeaders(params.token),
    body: JSON.stringify({
      username: params.username,
      role: params.role,
      question: params.question
    })
  });
}

export function getUsageStats(role: Role, token?: string): Promise<UsageStats> {
  return requestJson<UsageStats>(`/api/admin/usage-stats?role=${role}`, {
    headers: authHeaders(token)
  });
}

export function getAdminMetrics(role: Role, token?: string): Promise<AdminMetrics> {
  return requestJson<AdminMetrics>(`/api/admin/metrics?role=${role}`, {
    headers: authHeaders(token)
  });
}

export function getAgentLogs(
  role: Role,
  token?: string,
  filters?: {
    request_id?: string;
    username?: string;
    log_role?: string;
    intent?: string;
    risk_level?: string;
    success?: boolean | "";
  }
): Promise<AdminListResponse<AgentLog>> {
  const query = new URLSearchParams({ role, limit: "20" });
  setOptionalQuery(query, "request_id", filters?.request_id);
  setOptionalQuery(query, "username", filters?.username);
  setOptionalQuery(query, "log_role", filters?.log_role);
  setOptionalQuery(query, "intent", filters?.intent);
  setOptionalQuery(query, "risk_level", filters?.risk_level);
  setOptionalQuery(query, "success", filters?.success);
  return requestJson<AdminListResponse<AgentLog>>(
    `/api/admin/agent-call-logs?${query.toString()}`,
    { headers: authHeaders(token) }
  );
}

export function getAgentLogDetail(
  role: Role,
  callId: number,
  token?: string
): Promise<AgentLogDetail> {
  return requestJson<AgentLogDetail>(`/api/admin/agent-call-logs/${callId}?role=${role}`, {
    headers: authHeaders(token)
  });
}

export function getToolLogs(
  role: Role,
  token?: string,
  filters?: {
    request_id?: string;
    username?: string;
    log_role?: string;
    tool_name?: string;
    permission_allowed?: boolean | "";
    success?: boolean | "";
  }
): Promise<AdminListResponse<ToolLog>> {
  const query = new URLSearchParams({ role, limit: "20" });
  setOptionalQuery(query, "request_id", filters?.request_id);
  setOptionalQuery(query, "username", filters?.username);
  setOptionalQuery(query, "log_role", filters?.log_role);
  setOptionalQuery(query, "tool_name", filters?.tool_name);
  setOptionalQuery(query, "permission_allowed", filters?.permission_allowed);
  setOptionalQuery(query, "success", filters?.success);
  return requestJson<AdminListResponse<ToolLog>>(
    `/api/admin/tool-call-logs?${query.toString()}`,
    { headers: authHeaders(token) }
  );
}

export function getToolLogDetail(
  role: Role,
  logId: number,
  token?: string
): Promise<ToolLogDetail> {
  return requestJson<ToolLogDetail>(`/api/admin/tool-call-logs/${logId}?role=${role}`, {
    headers: authHeaders(token)
  });
}

export function searchKnowledge(params: {
  role: Role;
  query: string;
  token?: string;
}): Promise<{
  success: boolean;
  permission_allowed: boolean;
  query: string;
  results: KnowledgeResult[];
  message: string;
}> {
  const query = new URLSearchParams({
    role: params.role,
    query: params.query
  });
  return requestJson(`/api/knowledge/search?${query.toString()}`, {
    headers: authHeaders(params.token)
  });
}

export function getHealth(): Promise<{ status: string }> {
  return requestJson("/health");
}

export function getDeploymentStatus(token?: string): Promise<DeploymentStatusResponse> {
  return requestJson("/api/admin/deployment/status", {
    headers: authHeaders(token)
  });
}

export function getDeploymentLogs(params: {
  token?: string;
  service: string;
  tail?: number;
}): Promise<DeploymentLogResponse> {
  const query = new URLSearchParams({ tail: String(params.tail ?? 120) });
  return requestJson(`/api/admin/deployment/logs/${params.service}?${query.toString()}`, {
    headers: authHeaders(params.token)
  });
}

export function getDeploymentReport(params: {
  token?: string;
  reportId: string;
}): Promise<DeploymentReportResponse> {
  return requestJson(`/api/admin/deployment/reports/${params.reportId}`, {
    headers: authHeaders(params.token)
  });
}

export function getAuthPermissions(token?: string): Promise<{
  success: boolean;
  username: string;
  role: Role;
  permissions: string[];
}> {
  return requestJson("/api/auth/permissions", {
    headers: authHeaders(token)
  });
}

export function getMenus(token?: string): Promise<{
  success: boolean;
  username: string;
  role: Role;
  menus: ServerMenu[];
}> {
  return requestJson("/api/menus", {
    headers: authHeaders(token)
  });
}

export function submitPermissionRequest(params: {
  token?: string;
  requested_permission: string;
  reason: string;
  requested_role?: string;
}): Promise<{ success: boolean; data: PermissionRequest }> {
  return requestJson("/api/permissions/requests", {
    method: "POST",
    headers: authHeaders(params.token),
    body: JSON.stringify({
      requested_permission: params.requested_permission,
      requested_role: params.requested_role,
      reason: params.reason
    })
  });
}

export function getMyPermissionRequests(
  token?: string
): Promise<{ success: boolean; data: PermissionRequest[] }> {
  return requestJson("/api/permissions/requests/my", {
    headers: authHeaders(token)
  });
}

export function getAdminPermissionRequests(params: {
  token?: string;
  status?: string;
}): Promise<{ success: boolean; data: PermissionRequest[] }> {
  const query = params.status ? `?status=${params.status}` : "";
  return requestJson(`/api/admin/permission-requests${query}`, {
    headers: authHeaders(params.token)
  });
}

export function decidePermissionRequest(params: {
  token?: string;
  requestId: number;
  decision: "approve" | "reject";
  approval_comment?: string;
}): Promise<{ success: boolean; data: PermissionRequest }> {
  return requestJson(
    `/api/admin/permission-requests/${params.requestId}/${params.decision}`,
    {
      method: "POST",
      headers: authHeaders(params.token),
      body: JSON.stringify({ approval_comment: params.approval_comment })
    }
  );
}

export function getPermissionChangeLogs(params: {
  token?: string;
  source?: string;
  operator_username?: string;
  target_type?: string;
  target_identifier?: string;
  permission_code?: string;
  request_id?: string;
}): Promise<{ success: boolean; data: PermissionChangeLog[] }> {
  const query = new URLSearchParams();
  setOptionalQuery(query, "source", params.source);
  setOptionalQuery(query, "operator_username", params.operator_username);
  setOptionalQuery(query, "target_type", params.target_type);
  setOptionalQuery(query, "target_identifier", params.target_identifier);
  setOptionalQuery(query, "permission_code", params.permission_code);
  setOptionalQuery(query, "request_id", params.request_id);
  query.set("limit", "30");
  return requestJson(`/api/admin/permission-change-logs?${query.toString()}`, {
    headers: authHeaders(params.token)
  });
}

export function saveRolePermissions(params: {
  token?: string;
  role_code: Role;
  permission_codes: string[];
  remark: string;
}): Promise<{
  success: boolean;
  data: {
    role_code: string;
    permissions: string[];
    change_log_id: number;
    source: string;
    added: string[];
    removed: string[];
  };
}> {
  return requestJson(`/api/admin/role-permissions/${params.role_code}`, {
    method: "POST",
    headers: authHeaders(params.token),
    body: JSON.stringify({
      permission_codes: params.permission_codes,
      remark: params.remark
    })
  });
}
