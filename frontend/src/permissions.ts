import type { Role, ServerMenu } from "./types";

export type NavKey =
  | "chat"
  | "dashboard"
  | "audit"
  | "knowledge"
  | "permissions"
  | "approvals"
  | "deployment";

export type NavItem = {
  key: NavKey;
  label: string;
  adminOnly?: boolean;
};

export const navItems: NavItem[] = [
  { key: "chat", label: "业务问答" },
  { key: "dashboard", label: "运营看板", adminOnly: true },
  { key: "audit", label: "审计日志", adminOnly: true },
  { key: "knowledge", label: "知识库检索" },
  { key: "permissions", label: "权限中心" },
  { key: "approvals", label: "审批中心", adminOnly: true },
  { key: "deployment", label: "部署状态", adminOnly: true }
];

export const roleLabels: Record<Role, string> = {
  admin: "管理员",
  production_manager: "生产主管",
  sales: "销售",
  warehouse: "仓库",
  purchase: "采购",
  normal_user: "普通用户"
};

export type PermissionCatalogItem = {
  code: string;
  name: string;
  group: "menu" | "api" | "tool" | "document";
  menuPath: string[];
  requestable: boolean;
};

export const permissionCatalog: PermissionCatalogItem[] = [
  { code: "menu:chat", name: "业务问答菜单", group: "menu", menuPath: ["工作台", "业务问答"], requestable: true },
  { code: "menu:admin-dashboard", name: "运营看板菜单", group: "menu", menuPath: ["管理后台", "运营看板"], requestable: true },
  { code: "menu:audit-logs", name: "审计日志菜单", group: "menu", menuPath: ["管理后台", "审计日志"], requestable: true },
  { code: "menu:knowledge-search", name: "知识库检索菜单", group: "menu", menuPath: ["工作台", "知识库检索"], requestable: true },
  { code: "menu:permission-center", name: "权限中心菜单", group: "menu", menuPath: ["系统管理", "权限中心"], requestable: true },
  { code: "menu:approval-center", name: "审批中心菜单", group: "menu", menuPath: ["系统管理", "审批中心"], requestable: true },
  { code: "menu:deployment-status", name: "部署状态菜单", group: "menu", menuPath: ["系统管理", "部署状态"], requestable: false },
  { code: "api:admin-usage-stats", name: "用量统计 API", group: "api", menuPath: ["管理后台", "运营看板"], requestable: true },
  { code: "api:admin-agent-logs", name: "Agent 日志 API", group: "api", menuPath: ["管理后台", "审计日志"], requestable: true },
  { code: "api:admin-tool-logs", name: "工具日志 API", group: "api", menuPath: ["管理后台", "审计日志"], requestable: true },
  { code: "api:knowledge-rebuild", name: "知识库重建 API", group: "api", menuPath: ["系统管理", "知识库维护"], requestable: false },
  { code: "api:admin-permission-requests", name: "权限审批 API", group: "api", menuPath: ["系统管理", "审批中心"], requestable: true },
  { code: "api:admin-deployment-status", name: "部署状态 API", group: "api", menuPath: ["系统管理", "部署状态"], requestable: false },
  { code: "document:sop-public", name: "公开 SOP 文档", group: "document", menuPath: ["工作台", "知识库检索"], requestable: true },
  { code: "tool:query_order_status", name: "查询销售订单", group: "tool", menuPath: ["工作台", "业务问答", "订单"], requestable: true },
  { code: "tool:query_inventory_by_sku", name: "查询 SKU 库存", group: "tool", menuPath: ["工作台", "业务问答", "库存"], requestable: true },
  { code: "tool:query_work_order", name: "查询工单", group: "tool", menuPath: ["工作台", "业务问答", "工单"], requestable: true },
  { code: "tool:query_purchase_arrival", name: "查询采购到货", group: "tool", menuPath: ["工作台", "业务问答", "采购"], requestable: true },
  { code: "tool:query_exception_sop", name: "查询异常 SOP", group: "tool", menuPath: ["工作台", "业务问答", "SOP"], requestable: true },
  { code: "tool:analyze_order_delivery_risk", name: "分析订单交付风险", group: "tool", menuPath: ["工作台", "业务问答", "订单"], requestable: true },
  { code: "tool:analyze_work_order_readiness", name: "分析工单齐套", group: "tool", menuPath: ["工作台", "业务问答", "工单"], requestable: true },
  { code: "tool:analyze_purchase_delay_impact", name: "分析采购延期影响", group: "tool", menuPath: ["工作台", "业务问答", "采购"], requestable: true }
];

export const rolePermissionMatrix: Record<Role, string[]> = {
  admin: permissionCatalog.map((item) => item.code),
  production_manager: [
    "menu:chat",
    "menu:knowledge-search",
    "menu:permission-center",
    "document:sop-public",
    "tool:query_order_status",
    "tool:query_inventory_by_sku",
    "tool:query_work_order",
    "tool:query_purchase_arrival",
    "tool:query_exception_sop",
    "tool:analyze_order_delivery_risk",
    "tool:analyze_work_order_readiness",
    "tool:analyze_purchase_delay_impact"
  ],
  sales: [
    "menu:chat",
    "menu:knowledge-search",
    "menu:permission-center",
    "document:sop-public",
    "tool:query_order_status",
    "tool:query_inventory_by_sku",
    "tool:query_purchase_arrival",
    "tool:query_exception_sop",
    "tool:analyze_order_delivery_risk"
  ],
  warehouse: [
    "menu:chat",
    "menu:knowledge-search",
    "menu:permission-center",
    "document:sop-public",
    "tool:query_order_status",
    "tool:query_inventory_by_sku",
    "tool:query_purchase_arrival",
    "tool:query_exception_sop",
    "tool:analyze_order_delivery_risk"
  ],
  purchase: [
    "menu:chat",
    "menu:knowledge-search",
    "menu:permission-center",
    "document:sop-public",
    "tool:query_order_status",
    "tool:query_inventory_by_sku",
    "tool:query_purchase_arrival",
    "tool:query_exception_sop",
    "tool:analyze_order_delivery_risk",
    "tool:analyze_purchase_delay_impact"
  ],
  normal_user: [
    "menu:chat",
    "menu:knowledge-search",
    "menu:permission-center",
    "document:sop-public",
    "tool:query_exception_sop"
  ]
};

export const demoPermissions = rolePermissionMatrix;

export function visibleNavItems(role: Role): NavItem[] {
  return navItems.filter((item) => !item.adminOnly || role === "admin");
}

export function navItemsFromServerMenus(menus: ServerMenu[]): NavItem[] {
  const byKey = new Map(navItems.map((item) => [item.key, item]));
  return menus
    .map((menu) => {
      const item = byKey.get(menu.key as NavKey);
      if (!item) {
        return null;
      }
      return item;
    })
    .filter((item): item is NavItem => item !== null);
}
