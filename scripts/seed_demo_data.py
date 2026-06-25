from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path
import sys

from sqlalchemy import delete

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.audit import AgentCallLog, ToolCallLog, UsageStat
from app.models.auth import (
    ApiPermission,
    AuthUser,
    DocumentPermission,
    MenuPermission,
    Permission,
    Role,
    RolePermission,
    UserPermissionGrant,
    UserRole,
)
from app.models.inventory import InventoryBatch, InventorySku
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument
from app.models.order import SalesOrder, SalesOrderItem
from app.models.permission_change import PermissionChangeLog
from app.models.permission_request import PermissionRequest
from app.models.purchase import PurchaseOrder, PurchaseOrderItem
from app.models.user import UserAccount
from app.models.work_order import WorkOrder, WorkOrderMaterial
from app.services.auth_service import DEMO_PASSWORD, hash_password
from app.services.knowledge_service import rebuild_knowledge


def seed_demo_data() -> None:
    init_db()
    db = SessionLocal()
    try:
        for model in [
            ToolCallLog,
            AgentCallLog,
            UsageStat,
            PermissionChangeLog,
            PermissionRequest,
            KnowledgeChunk,
            KnowledgeDocument,
            WorkOrderMaterial,
            WorkOrder,
            PurchaseOrderItem,
            PurchaseOrder,
            SalesOrderItem,
            SalesOrder,
            InventoryBatch,
            InventorySku,
            UserAccount,
            UserPermissionGrant,
            RolePermission,
            UserRole,
            ApiPermission,
            DocumentPermission,
            MenuPermission,
            Permission,
            Role,
            AuthUser,
        ]:
            db.execute(delete(model))

        users = [
            ("demo_admin", "管理员", "admin"),
            ("demo_pm", "生产主管", "production_manager"),
            ("demo_sales", "销售", "sales"),
            ("demo_warehouse", "仓库", "warehouse"),
            ("demo_purchase", "采购", "purchase"),
            ("demo_user", "普通用户", "normal_user"),
        ]
        for username, display_name, role in users:
            db.add(
                UserAccount(
                    username=username,
                    display_name=display_name,
                    role=role,
                    is_active=True,
                )
            )

        role_names = {
            "admin": "管理员",
            "production_manager": "生产主管",
            "sales": "销售",
            "warehouse": "仓库",
            "purchase": "采购",
            "normal_user": "普通用户",
        }
        for role_code, role_name in role_names.items():
            db.add(Role(code=role_code, name=role_name))
        db.flush()

        permission_rows = [
            ("menu:chat", "Chat 工作台", "menu"),
            ("menu:admin-dashboard", "Admin Dashboard", "menu"),
            ("menu:audit-logs", "Audit Logs", "menu"),
            ("menu:knowledge-search", "Knowledge Search", "menu"),
            ("menu:permission-center", "Permission Center", "menu"),
            ("menu:approval-center", "Admin Approval Center", "menu"),
            ("menu:deployment-status", "Deployment Status", "menu"),
            ("api:admin-usage-stats", "Usage stats API", "api"),
            ("api:admin-agent-logs", "Agent logs API", "api"),
            ("api:admin-tool-logs", "Tool logs API", "api"),
            ("api:knowledge-rebuild", "Knowledge rebuild API", "api"),
            (
                "api:admin-permission-requests",
                "Admin permission request API",
                "api",
            ),
            ("api:admin-deployment-status", "Deployment status API", "api"),
            ("document:sop-public", "Public SOP documents", "document"),
            ("tool:query_order_status", "query_order_status", "tool"),
            ("tool:query_inventory_by_sku", "query_inventory_by_sku", "tool"),
            ("tool:query_work_order", "query_work_order", "tool"),
            ("tool:query_purchase_arrival", "query_purchase_arrival", "tool"),
            ("tool:query_exception_sop", "query_exception_sop", "tool"),
            ("tool:analyze_order_delivery_risk", "analyze_order_delivery_risk", "tool"),
            ("tool:analyze_work_order_readiness", "analyze_work_order_readiness", "tool"),
            ("tool:analyze_purchase_delay_impact", "analyze_purchase_delay_impact", "tool"),
        ]
        for code, name, category in permission_rows:
            db.add(Permission(code=code, name=name, category=category))
        db.flush()

        menu_rows = [
            ("chat", "Chat 工作台", "menu:chat", 10),
            ("dashboard", "Admin Dashboard", "menu:admin-dashboard", 20),
            ("audit", "Audit Logs", "menu:audit-logs", 30),
            ("knowledge", "Knowledge Search", "menu:knowledge-search", 40),
            ("permissions", "Permission Center", "menu:permission-center", 50),
            ("approvals", "Admin Approval Center", "menu:approval-center", 60),
            ("deployment", "Deployment Status", "menu:deployment-status", 70),
        ]
        for menu_key, label, permission_code, sort_order in menu_rows:
            db.add(
                MenuPermission(
                    menu_key=menu_key,
                    label=label,
                    permission_code=permission_code,
                    sort_order=sort_order,
                )
            )

        for method, path, permission_code in [
            ("GET", "/api/admin/usage-stats", "api:admin-usage-stats"),
            ("GET", "/api/admin/agent-call-logs", "api:admin-agent-logs"),
            ("GET", "/api/admin/tool-call-logs", "api:admin-tool-logs"),
            ("GET", "/api/admin/deployment/status", "api:admin-deployment-status"),
            ("GET", "/api/admin/deployment/logs", "api:admin-deployment-status"),
            ("POST", "/api/knowledge/rebuild", "api:knowledge-rebuild"),
        ]:
            db.add(ApiPermission(method=method, path=path, permission_code=permission_code))
        db.add(
            DocumentPermission(
                document_scope="sop-public", permission_code="document:sop-public"
            )
        )

        role_permissions = {
            "admin": [code for code, _, _ in permission_rows],
            "production_manager": [
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
                "tool:analyze_purchase_delay_impact",
            ],
            "sales": [
                "menu:chat",
                "menu:knowledge-search",
                "menu:permission-center",
                "document:sop-public",
                "tool:query_order_status",
                "tool:query_inventory_by_sku",
                "tool:query_purchase_arrival",
                "tool:query_exception_sop",
                "tool:analyze_order_delivery_risk",
            ],
            "warehouse": [
                "menu:chat",
                "menu:knowledge-search",
                "menu:permission-center",
                "document:sop-public",
                "tool:query_order_status",
                "tool:query_inventory_by_sku",
                "tool:query_purchase_arrival",
                "tool:query_exception_sop",
                "tool:analyze_order_delivery_risk",
            ],
            "purchase": [
                "menu:chat",
                "menu:knowledge-search",
                "menu:permission-center",
                "document:sop-public",
                "tool:query_order_status",
                "tool:query_inventory_by_sku",
                "tool:query_purchase_arrival",
                "tool:query_exception_sop",
                "tool:analyze_order_delivery_risk",
                "tool:analyze_purchase_delay_impact",
            ],
            "normal_user": [
                "menu:chat",
                "menu:knowledge-search",
                "menu:permission-center",
                "document:sop-public",
                "tool:query_exception_sop",
            ],
        }
        for role_code, permission_codes in role_permissions.items():
            for permission_code in permission_codes:
                db.add(
                    RolePermission(
                        role_code=role_code,
                        permission_code=permission_code,
                    )
                )

        password_hash = hash_password(DEMO_PASSWORD)
        for username, display_name, role in users:
            db.add(
                AuthUser(
                    username=username,
                    display_name=display_name,
                    password_hash=password_hash,
                    is_active=True,
                )
            )
            db.add(UserRole(username=username, role_code=role))
        db.flush()

        db.add(
            SalesOrder(
                order_no="O1001",
                customer_name="东莞凯博电器有限公司",
                order_status="confirmed",
                delivery_status="pending",
                planned_delivery_date=date.today() + timedelta(days=2),
            )
        )
        db.add(
            SalesOrderItem(
                order_no="O1001",
                sku_code="SKU-KB-001",
                sku_name="控制面板注塑件",
                quantity=Decimal("120.00"),
                delivered_quantity=Decimal("0.00"),
                locked_quantity=Decimal("80.00"),
            )
        )

        db.add(
            InventorySku(
                sku_code="SKU-KB-001",
                sku_name="控制面板注塑件",
                total_quantity=Decimal("150.00"),
                available_quantity=Decimal("100.00"),
                locked_quantity=Decimal("50.00"),
                quality_hold_quantity=Decimal("20.00"),
                unit="pcs",
            )
        )
        db.add(
            InventoryBatch(
                sku_code="SKU-KB-001",
                batch_no="BATCH-KB-202601",
                warehouse_code="WH-DG-01",
                quantity=Decimal("150.00"),
                available_quantity=Decimal("100.00"),
                locked_quantity=Decimal("50.00"),
                quality_hold_quantity=Decimal("20.00"),
                production_date=date(2026, 1, 10),
                expire_date=date(2027, 1, 10),
            )
        )
        db.add(
            InventorySku(
                sku_code="MAT-ABS-001",
                sku_name="ABS 原料",
                total_quantity=Decimal("80.00"),
                available_quantity=Decimal("80.00"),
                locked_quantity=Decimal("0.00"),
                quality_hold_quantity=Decimal("0.00"),
                unit="kg",
            )
        )
        db.add(
            InventoryBatch(
                sku_code="MAT-ABS-001",
                batch_no="BATCH-ABS-202606",
                warehouse_code="WH-DG-01",
                quantity=Decimal("80.00"),
                available_quantity=Decimal("80.00"),
                locked_quantity=Decimal("0.00"),
                quality_hold_quantity=Decimal("0.00"),
                production_date=date(2026, 6, 1),
                expire_date=date(2027, 6, 1),
            )
        )
        db.add(
            InventorySku(
                sku_code="MAT-COLOR-001",
                sku_name="黑色母粒",
                total_quantity=Decimal("10.00"),
                available_quantity=Decimal("10.00"),
                locked_quantity=Decimal("0.00"),
                quality_hold_quantity=Decimal("0.00"),
                unit="kg",
            )
        )
        db.add(
            InventoryBatch(
                sku_code="MAT-COLOR-001",
                batch_no="BATCH-COLOR-202606",
                warehouse_code="WH-DG-01",
                quantity=Decimal("10.00"),
                available_quantity=Decimal("10.00"),
                locked_quantity=Decimal("0.00"),
                quality_hold_quantity=Decimal("0.00"),
                production_date=date(2026, 6, 5),
                expire_date=date(2027, 6, 5),
            )
        )

        db.add(
            WorkOrder(
                work_order_no="WO1001",
                product_sku="SKU-KB-001",
                product_name="控制面板注塑件",
                planned_quantity=Decimal("200.00"),
                finished_quantity=Decimal("0.00"),
                status="planned",
                planned_start_date=date.today(),
                planned_end_date=date.today() + timedelta(days=1),
                expected_replenishment_date=date.today() + timedelta(days=1),
            )
        )
        db.add(
            WorkOrderMaterial(
                work_order_no="WO1001",
                material_sku="MAT-ABS-001",
                material_name="ABS 原料",
                required_quantity=Decimal("120.00"),
                issued_quantity=Decimal("0.00"),
            )
        )
        db.add(
            WorkOrderMaterial(
                work_order_no="WO1001",
                material_sku="MAT-COLOR-001",
                material_name="黑色母粒",
                required_quantity=Decimal("8.00"),
                issued_quantity=Decimal("0.00"),
            )
        )

        db.add(
            PurchaseOrder(
                purchase_order_no="PO1001",
                supplier_name="华南塑胶原料供应商",
                status="delayed",
                expected_arrival_date=date.today() + timedelta(days=3),
                is_delayed=True,
            )
        )
        db.add(
            PurchaseOrderItem(
                purchase_order_no="PO1001",
                sku_code="SKU-KB-001",
                sku_name="控制面板注塑件",
                quantity=Decimal("80.00"),
                arrived_quantity=Decimal("0.00"),
            )
        )

        db.commit()
        rebuild_knowledge(db)
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
    print("Demo data seeded.")
