import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import App from "./App";

function jsonResponse(data: unknown, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" }
  });
}

const pendingPermissionRequest = {
  id: 101,
  requester_username: "demo_user",
  requested_permission: "menu:admin-dashboard",
  requested_role: null,
  reason: "需要查看 usage dashboard 以排查演示调用情况。",
  status: "pending",
  approver_username: null,
  approval_comment: null,
  created_at: "2026-06-24T12:00:00",
  decided_at: null
};

beforeEach(() => {
  window.history.pushState({}, "", "/");
  let permissionRequests = [{ ...pendingPermissionRequest }];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string, init?: RequestInit) => {
      const path = String(url);
      const headers = new Headers(init?.headers);
      const token = headers.get("Authorization") ?? "";
      const roleFromToken = token.includes("admin") ? "admin" : "normal_user";
      const withoutChat = token.includes("without-chat");
      const expireOnDashboard = token.includes("expire-on-dashboard");
      const denyDashboard = token.includes("deny-dashboard");

      if (path.endsWith("/api/menus")) {
        const menus =
          roleFromToken === "admin"
            ? [
                { key: "chat", label: "Chat Workbench", permission_code: "menu:chat" },
                {
                  key: "dashboard",
                  label: "Admin Dashboard",
                  permission_code: "menu:admin-dashboard"
                },
                { key: "audit", label: "Audit Logs", permission_code: "menu:audit-logs" },
                {
                  key: "knowledge",
                  label: "Knowledge Search",
                  permission_code: "menu:knowledge-search"
                },
                {
                  key: "permissions",
                  label: "Permission Center",
                  permission_code: "menu:permission-center"
                },
                {
                  key: "approvals",
                  label: "Admin Approval Center",
                  permission_code: "menu:approval-center"
                },
                {
                  key: "deployment",
                  label: "Deployment Status",
                  permission_code: "menu:deployment-status"
                }
              ]
            : withoutChat
              ? [
                  {
                    key: "knowledge",
                    label: "Knowledge Search",
                    permission_code: "menu:knowledge-search"
                  },
                  {
                    key: "permissions",
                    label: "Permission Center",
                    permission_code: "menu:permission-center"
                  }
                ]
              : [
                { key: "chat", label: "Chat Workbench", permission_code: "menu:chat" },
                {
                  key: "knowledge",
                  label: "Knowledge Search",
                  permission_code: "menu:knowledge-search"
                },
                {
                  key: "permissions",
                  label: "Permission Center",
                  permission_code: "menu:permission-center"
                }
              ];
        return jsonResponse({
          success: true,
          username: roleFromToken === "admin" ? "demo_admin" : "demo_user",
          role: roleFromToken,
          menus
        });
      }

      if (path.endsWith("/api/auth/permissions")) {
        const permissions =
          roleFromToken === "admin"
            ? ["menu:admin-dashboard", "api:admin-agent-logs", "tool:*"]
            : [
                "menu:chat",
                "menu:knowledge-search",
                "menu:permission-center",
                "document:sop-public"
              ];
        return jsonResponse({
          success: true,
          username: roleFromToken === "admin" ? "demo_admin" : "demo_user",
          role: roleFromToken,
          permissions
        });
      }

      if (path.includes("/api/admin/usage-stats")) {
        if (expireOnDashboard) {
          return jsonResponse({ error: { message: "token expired" } }, 401);
        }
        if (denyDashboard) {
          return jsonResponse({ error: { message: "permission denied" } }, 403);
        }
        return jsonResponse({
          success: true,
          total_agent_calls: 7,
          total_tool_calls: 12,
          permission_denied_count: 2,
          success_rate: 0.875,
          denied_rate: 0.1667,
          avg_latency_ms: 42,
          top_tools: [["query_exception_sop", 4]],
          top_intents: [["exception_sop", 3]]
        });
      }

      if (path.includes("/api/admin/metrics")) {
        if (expireOnDashboard) {
          return jsonResponse({ error: { message: "token expired" } }, 401);
        }
        if (denyDashboard) {
          return jsonResponse({ error: { message: "permission denied" } }, 403);
        }
        return jsonResponse({
          success: true,
          total_requests: 9,
          total_agent_calls: 7,
          total_tool_calls: 12,
          success_rate: 0.875,
          denied_rate: 0.1667,
          avg_latency_ms: 42,
          high_risk_count: 1
        });
      }

      const agentDetailMatch = path.match(/\/api\/admin\/agent-call-logs\/(\d+)/);
      if (agentDetailMatch) {
        return jsonResponse({
          success: true,
          call_id: Number(agentDetailMatch[1]),
          question: "订单 O1001 现在能不能发货？",
          user_role: "sales",
          username: "demo_sales",
          intent: "order_delivery_risk",
          entities: { order_id: "O1001" },
          risk_level: "medium",
          answer_summary: "库存可用但需要人工确认。",
          response_json: {
            decision_record: {
              plan: ["query_order_status", "query_inventory_by_sku"]
            }
          },
          decision_record: {
            plan: ["query_order_status", "query_inventory_by_sku"]
          },
          execution_trace: [{ step: "permission_check", status: "allowed" }],
          tool_calls: [
            {
              tool_name: "query_order_status",
              status: "success",
              allowed: true
            }
          ],
          created_at: "2026-06-24T12:00:00"
        });
      }

      if (path.includes("/api/admin/agent-call-logs")) {
        return jsonResponse({
          success: true,
          data: [
            {
              id: 501,
              username: "demo_sales",
              role: "sales",
              question: "订单 O1001 现在能不能发货？",
              success: true,
              intent: "order_delivery_risk",
              risk_level: "medium",
              latency_ms: 88,
              created_at: "2026-06-24T12:00:00"
            }
          ]
        });
      }

      const toolDetailMatch = path.match(/\/api\/admin\/tool-call-logs\/(\d+)/);
      if (toolDetailMatch) {
        return jsonResponse({
          success: true,
          id: Number(toolDetailMatch[1]),
          request_id: "smoke-request-id",
          agent_call_id: 501,
          username: "demo_sales",
          role: "sales",
          tool_name: "query_order_status",
          status: "success",
          permission_allowed: true,
          success_flag: true,
          tool_args_json: { order_no: "O1001" },
          tool_result_summary: "order status checked",
          error_message: null,
          latency_ms: 8,
          created_at: "2026-06-24T12:00:00"
        });
      }

      if (path.includes("/api/admin/tool-call-logs")) {
        return jsonResponse({
          success: true,
          data: [
            {
              id: 601,
              username: "demo_sales",
              role: "sales",
              tool_name: "query_order_status",
              permission_allowed: true,
              success: true,
              latency_ms: 8,
              created_at: "2026-06-24T12:00:00"
            }
          ]
        });
      }

      if (path.includes("/api/knowledge/search")) {
        return jsonResponse({
          success: true,
          permission_allowed: true,
          query: "注塑件外观不良应该怎么处理？",
          results: [
            {
              doc_title: "注塑件外观不良处理 SOP",
              source_path: "docs/sop/injection_defect.md",
              score: 0.91,
              matched_terms: ["注塑件", "外观不良"],
              chunk_text: "先隔离疑似不良批次，确认缺陷类型并通知质量人员复核。"
            }
          ],
          message: "ok"
        });
      }

      if (path.endsWith("/health")) {
        return jsonResponse({ status: "ok" });
      }

      if (path.endsWith("/api/admin/deployment/status")) {
        return jsonResponse({
          success: true,
          source: "docker_compose",
          environment: "test",
          app: "manufacturing-ai-agent",
          version: "0.1.0",
          checked_at: "2026-06-25T12:00:00",
          services: [
            { name: "backend", state: "running", image: "backend:test", health: "healthy" },
            { name: "nginx", state: "running", image: "nginx:test", health: "" }
          ],
          docker_available: true,
          message: "Docker Compose status read.",
          report_files: [
            {
              id: "cloud-deployment-check-report",
              label: "cloud deployment report",
              path: "docs/cloud-deployment-check-report.md",
              exists: true
            }
          ]
        });
      }

      if (path.includes("/api/admin/deployment/reports/")) {
        const reportId = path.split("/api/admin/deployment/reports/")[1] ?? "demo-report";
        return jsonResponse({
          success: true,
          id: reportId,
          label: "cloud deployment report",
          path: "docs/cloud-deployment-check-report.md",
          content: "# Cloud Deployment Check Report\n\nReport content stays unchanged.",
          checked_at: "2026-06-25T12:00:00"
        });
      }

      if (path.includes("/api/admin/deployment/logs/")) {
        const service = path.split("/api/admin/deployment/logs/")[1]?.split("?")[0] ?? "backend";
        return jsonResponse({
          success: true,
          service,
          source: "docker_compose_logs",
          tail: 120,
          available: true,
          lines: [`${service} log line 1`, `${service} log line 2`],
          message: "Docker Compose logs read.",
          readonly_command: `docker compose logs --tail 120 ${service}`,
          checked_at: "2026-06-25T12:00:00"
        });
      }

      if (path.endsWith("/api/chat")) {
        const body = JSON.parse(String(init?.body ?? "{}"));
        expect(Object.keys(body).sort()).toEqual(["question", "role", "username"]);
        return jsonResponse({
          success: true,
          question: "订单 O1001 现在能不能发货？",
          answer: "订单 O1001 已检查销售订单、库存和采购到货信息；当前建议人工确认后再发货。",
          checked_data: ["sales_order:O1001", "inventory:SKU-KB-001"],
          called_tools: [
            {
              success: true,
              permission_allowed: true,
              tool_name: "query_order_status",
              data: { order_id: "O1001" },
              message: "订单状态查询完成",
              manual_confirmation_required: true
            },
            {
              success: true,
              permission_allowed: true,
              tool_name: "query_inventory_by_sku",
              data: { sku: "SKU-KB-001" },
              message: "库存查询完成",
              manual_confirmation_required: true
            }
          ],
          business_conclusion: "可发货但需要仓库和销售人工确认。",
          suggested_next_action: "请仓库复核批次和锁定库存后再执行发货。",
          intent: "order_delivery_risk",
          entities: { order_id: "O1001" },
          execution_trace: [{ step: "permission_check", status: "allowed" }],
          risk_level: "medium",
          evidence: ["库存批次 BATCH-KB-202601 可用"],
          recommendations: ["人工确认后再执行任何业务动作"],
          risk_factors: ["存在锁定库存，需要复核可用数量"],
          requires_human_review: true,
          manual_review_reason: ["发货属于高风险业务动作，需要人工确认"],
          decision_record: {
            plan: ["query_order_status", "query_inventory_by_sku"],
            permission_results: ["query_order_status allowed", "query_inventory_by_sku allowed"]
          },
          manual_confirmation_required: true
        });
      }

      if (path.includes("/api/permissions/requests/my")) {
        return jsonResponse({ success: true, data: permissionRequests });
      }

      if (path.includes("/api/admin/permission-change-logs")) {
        return jsonResponse({
          success: true,
          data: [
            {
              id: 1,
              source: "request_approval",
              operator_username: "demo_admin",
              target_type: "user",
              target_identifier: "demo_user",
              permission_code: "menu:admin-dashboard",
              before_value: { granted: false },
              after_value: { granted: true },
              diff: { decision: "approved", granted: true },
              remark: "Reason checked by admin.",
              request_id: 101,
              created_at: "2026-06-24T12:10:00"
            }
          ]
        });
      }

      if (path.endsWith("/api/permissions/requests")) {
        const body = JSON.parse(String(init?.body ?? "{}"));
        const created = {
          ...pendingPermissionRequest,
          id: permissionRequests.length + 200,
          requested_permission: body.requested_permission,
          reason: body.reason
        };
        permissionRequests = [created, ...permissionRequests];
        return jsonResponse({ success: true, data: created });
      }

      if (path.includes("/api/admin/permission-requests")) {
        if (path.endsWith("/approve") || path.endsWith("/reject")) {
          const decision = path.endsWith("/approve") ? "approved" : "rejected";
          const match = path.match(/permission-requests\/(\d+)\/(approve|reject)$/);
          const requestId = Number(match?.[1]);
          const existing = permissionRequests.find((item) => item.id === requestId);
          const decided = {
            ...(existing ?? pendingPermissionRequest),
            id: requestId,
            status: decision,
            approver_username: "demo_admin",
            approval_comment: "仅授予平台菜单访问权限。",
            decided_at: "2026-06-24T12:10:00"
          };
          permissionRequests = permissionRequests.filter((item) => item.id !== requestId);
          return jsonResponse({ success: true, data: decided });
        }
        return jsonResponse({
          success: true,
          data: permissionRequests.filter((item) => item.status === "pending")
        });
      }

      const body = JSON.parse(String(init?.body ?? "{}"));
      const role =
        body.username === "demo_admin" ||
        body.username === "expire_admin" ||
        body.username === "forbidden_admin"
          ? "admin"
          : "normal_user";
      const tokenSuffix =
        body.username === "without_chat"
          ? "without-chat"
          : body.username === "expire_admin"
            ? "expire-on-dashboard-admin"
            : body.username === "forbidden_admin"
              ? "deny-dashboard-admin"
            : role;
      return jsonResponse({
        success: true,
        access_token: `test-token-${tokenSuffix}`,
        token_type: "bearer",
        user: {
          username: body.username,
          display_name: body.username,
          role
        }
      });
    })
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  window.history.pushState({}, "", "/");
});

async function loginAs(role: string, username = "demo_user") {
  render(<App />);
  await userEvent.clear(screen.getByLabelText("用户名"));
  await userEvent.type(screen.getByLabelText("用户名"), username);
  await userEvent.selectOptions(screen.getByLabelText("角色"), role);
  await userEvent.click(screen.getByRole("button", { name: "进入控制台" }));
}

describe("P8 console smoke", () => {
  it("uses server RBAC menus and hides admin navigation from normal_user", async () => {
    await loginAs("normal_user");

    expect(screen.getByRole("button", { name: /业务问答/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /知识库检索/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /权限中心/ })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /运营看板/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /审计日志/ })).not.toBeInTheDocument();
  });

  it("allows admin to access dashboard and audit menus from server RBAC", async () => {
    await loginAs("admin", "demo_admin");

    expect(screen.getByRole("button", { name: /运营看板/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /审计日志/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /审批中心/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /部署状态/ })).toBeInTheDocument();
  });

  it("loads usage stats and operational metrics on admin dashboard", async () => {
    await loginAs("admin", "demo_admin");

    await userEvent.click(screen.getByRole("button", { name: /运营看板/ }));
    await userEvent.click(screen.getByRole("button", { name: /用量统计/ }));

    expect(screen.getByText("运行指标")).toBeInTheDocument();
    expect(screen.getByText("总请求数")).toBeInTheDocument();
    expect(screen.getByText("高风险次数")).toBeInTheDocument();
  });

  it("shows a clear permission message when an admin page API returns 403", async () => {
    await loginAs("admin", "forbidden_admin");

    await userEvent.click(screen.getByRole("button", { name: /运营看板/ }));
    await userEvent.click(screen.getByRole("button", { name: /用量统计/ }));

    expect(await screen.findByText("当前账号没有访问该功能的权限。")).toBeInTheDocument();
  });

  it("renders chat answer, tool permissions, risk factors, manual review, and decision record", async () => {
    await loginAs("normal_user");

    await userEvent.click(screen.getByRole("button", { name: "开始分析" }));

    expect(await screen.findByText(/订单 O1001 已检查销售订单/)).toBeInTheDocument();
    expect(screen.getByText("查询销售订单")).toBeInTheDocument();
    expect(screen.getAllByText("已授权").length).toBeGreaterThan(0);
    expect(screen.getByText(/存在锁定库存/)).toBeInTheDocument();
    expect(screen.getByText(/发货属于高风险业务动作/)).toBeInTheDocument();
    expect(screen.getByText(/permission_results/)).toBeInTheDocument();
  });

  it("loads audit logs and fetches agent call detail", async () => {
    await loginAs("admin", "demo_admin");

    await userEvent.click(screen.getByRole("button", { name: /审计日志/ }));
    await userEvent.click(screen.getByRole("button", { name: "刷新" }));

    await userEvent.click(await screen.findByRole("button", { name: /order_delivery_risk/ }));

    expect(await screen.findByText(/query_order_status/)).toBeInTheDocument();
    expect(screen.getByText(/decision_record/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /查询销售订单/ }));
    expect(await screen.findByText(/tool_args_json/)).toBeInTheDocument();
    expect(screen.getByText(/O1001/)).toBeInTheDocument();
  });

  it("renders SOP knowledge search result details", async () => {
    await loginAs("normal_user");

    await userEvent.click(screen.getByRole("button", { name: /知识库检索/ }));
    await userEvent.click(screen.getByRole("button", { name: "检索 SOP" }));

    expect(await screen.findByText("注塑件外观不良处理 SOP")).toBeInTheDocument();
    expect(screen.getByText("docs/sop/injection_defect.md")).toBeInTheDocument();
    expect(screen.getByText("score: 0.91")).toBeInTheDocument();
    expect(screen.getByText("matched: 注塑件, 外观不良")).toBeInTheDocument();
  });

  it("shows server RBAC permissions in permission center", async () => {
    await loginAs("normal_user");

    await userEvent.click(screen.getByRole("button", { name: /权限中心/ }));

    expect(screen.getByRole("heading", { name: "角色权限矩阵" })).toBeInTheDocument();
    expect(screen.getAllByText("公开 SOP 文档").length).toBeGreaterThan(0);
    expect(screen.getAllByText("查询异常 SOP").length).toBeGreaterThan(0);
    expect(screen.queryByText("tool:*")).not.toBeInTheDocument();
  });

  it("lets a normal user submit a platform permission request", async () => {
    await loginAs("normal_user");

    await userEvent.click(screen.getByRole("button", { name: /权限中心/ }));
    await userEvent.click(screen.getByRole("button", { name: "提交权限申请" }));

    expect((await screen.findAllByText(/menu:admin-dashboard/)).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/pending/).length).toBeGreaterThan(0);
  });

  it("lets admin approve pending platform permission requests", async () => {
    await loginAs("admin", "demo_admin");

    await userEvent.click(screen.getByRole("button", { name: /审批中心/ }));
    await userEvent.click(screen.getByRole("button", { name: /刷新待审批/ }));

    expect(await screen.findByText("demo_user")).toBeInTheDocument();
    expect(screen.getByText(/menu:admin-dashboard/)).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "通过" }));

    expect(await screen.findByText("暂无待审批权限申请。")).toBeInTheDocument();
  });

  it("does not fall back to chat when server RBAC omits the chat menu", async () => {
    await loginAs("normal_user", "without_chat");

    expect(screen.queryByRole("button", { name: /业务问答/ })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /知识库检索/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /知识库检索/ })).toBeInTheDocument();
  });

  it("returns to login when a token expires during an authenticated request", async () => {
    await loginAs("admin", "expire_admin");

    await userEvent.click(screen.getByRole("button", { name: /运营看板/ }));

    expect(await screen.findByText("登录已过期或未登录，请重新登录。")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "进入控制台" })).toBeInTheDocument();
  });

  it("checks deployment health from the React deployment status page", async () => {
    await loginAs("admin", "demo_admin");

    await userEvent.click(screen.getByRole("button", { name: /部署状态/ }));
    await userEvent.click(screen.getByRole("button", { name: "检查健康状态" }));

    expect(await screen.findByText("健康检查")).toBeInTheDocument();
    expect(screen.getByText("ok")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "日志查看" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "后端服务" })).toBeInTheDocument();
    expect(screen.getByText("高频查看区域，日志内容保持原文")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "服务状态" }));
    expect(await screen.findByText("中频查看，点击服务可切换日志")).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: "部署报告" }));
    expect(await screen.findByText("低频查看，文件名保持原样")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "查看" }));
    expect(await screen.findByText(/Cloud Deployment Check Report/)).toBeInTheDocument();
  });

  it("shows a 404 page for unknown routes before login", () => {
    window.history.pushState({}, "", "/not-a-real-page");

    render(<App />);

    expect(screen.getByRole("heading", { name: "页面不存在" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "进入控制台" })).not.toBeInTheDocument();
  });
});
