export type Role =
  | "admin"
  | "production_manager"
  | "sales"
  | "warehouse"
  | "purchase"
  | "normal_user";

export type SessionUser = {
  username: string;
  role: Role;
  token?: string;
  displayName?: string;
  menus?: ServerMenu[];
  permissions?: string[];
};

export type ServerMenu = {
  key: string;
  label: string;
  permission_code: string;
};

export type ToolCall = {
  success: boolean;
  permission_allowed: boolean;
  tool_name: string;
  data?: unknown;
  message: string;
  manual_confirmation_required: boolean;
};

export type ChatResponse = {
  success: boolean;
  question: string;
  answer: string;
  checked_data: string[];
  called_tools: ToolCall[];
  business_conclusion: string;
  suggested_next_action: string;
  intent: string;
  entities: Record<string, unknown>;
  execution_trace: Array<Record<string, unknown>>;
  risk_level: string;
  evidence: string[];
  recommendations: string[];
  risk_factors: string[];
  requires_human_review: boolean;
  manual_review_reason: string[];
  decision_record: Record<string, unknown>;
  manual_confirmation_required: boolean;
};

export type UsageStats = {
  success: boolean;
  total_agent_calls: number;
  total_tool_calls: number;
  permission_denied_count: number;
  success_rate: number;
  denied_rate: number;
  avg_latency_ms: number;
  top_tools: Array<[string, number]>;
  top_intents: Array<[string, number]>;
};

export type AdminMetrics = {
  success: boolean;
  total_requests: number;
  total_agent_calls: number;
  total_tool_calls: number;
  success_rate: number;
  denied_rate: number;
  avg_latency_ms: number;
  high_risk_count: number;
};

export type AdminListResponse<T> = {
  success: boolean;
  data: T[];
};

export type AgentLog = {
  id: number;
  username: string;
  role: string;
  question: string;
  success: boolean;
  intent?: string;
  risk_level?: string;
  latency_ms?: number;
  created_at?: string;
};

export type AgentLogDetail = {
  success: boolean;
  call_id: number;
  question: string;
  user_role: string;
  username: string;
  intent: string;
  entities: Record<string, unknown>;
  risk_level: string;
  answer_summary?: string;
  response_json: Record<string, unknown>;
  decision_record: Record<string, unknown>;
  execution_trace: Array<Record<string, unknown>>;
  tool_calls: Array<Record<string, unknown>>;
  created_at?: string;
};

export type ToolLog = {
  id: number;
  username: string;
  role: string;
  tool_name: string;
  permission_allowed: boolean;
  success: boolean;
  latency_ms?: number;
  created_at?: string;
  error_message?: string;
};

export type ToolLogDetail = ToolLog & {
  success: boolean;
  request_id?: string | null;
  agent_call_id?: number | null;
  status: string;
  success_flag: boolean;
  tool_args_json: Record<string, unknown>;
  tool_result_summary?: string | null;
};

export type PermissionChangeLog = {
  id: number;
  source: "request_approval" | "admin_direct_change" | "system_seed" | string;
  operator_username: string;
  target_type: "user" | "role" | string;
  target_identifier: string;
  permission_code?: string | null;
  before_value?: Record<string, unknown> | null;
  after_value?: Record<string, unknown> | null;
  diff?: Record<string, unknown> | null;
  remark: string;
  request_id?: number | null;
  created_at?: string;
};

export type DeploymentServiceStatus = {
  name: string;
  state: string;
  image?: string;
  health?: string;
  published_ports?: unknown;
};

export type DeploymentStatusResponse = {
  success: boolean;
  source: string;
  environment: string;
  app: string;
  version: string;
  checked_at: string;
  services: DeploymentServiceStatus[];
  docker_available: boolean;
  message: string;
  report_files: Array<{ id?: string; label: string; path: string; exists: boolean }>;
};

export type DeploymentLogResponse = {
  success: boolean;
  service: string;
  source: string;
  tail: number;
  available: boolean;
  lines: string[];
  message: string;
  readonly_command: string;
  checked_at: string;
};

export type DeploymentReportResponse = {
  success: boolean;
  id: string;
  label: string;
  path: string;
  content: string;
  checked_at: string;
};

export type KnowledgeResult = {
  doc_title: string;
  source_path: string;
  score: number;
  matched_terms: string[];
  chunk_text: string;
};

export type PermissionRequest = {
  id: number;
  requester_username: string;
  requested_permission: string;
  requested_role?: string | null;
  reason: string;
  status: "pending" | "approved" | "rejected";
  approver_username?: string | null;
  approval_comment?: string | null;
  created_at?: string;
  decided_at?: string | null;
};
