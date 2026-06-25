from enum import StrEnum


class Role(StrEnum):
    ADMIN = "admin"
    PRODUCTION_MANAGER = "production_manager"
    SALES = "sales"
    WAREHOUSE = "warehouse"
    PURCHASE = "purchase"
    NORMAL_USER = "normal_user"


TOOL_PERMISSIONS: dict[str, set[str]] = {
    "query_order_status": {
        Role.ADMIN,
        Role.PRODUCTION_MANAGER,
        Role.SALES,
        Role.WAREHOUSE,
        Role.PURCHASE,
    },
    "query_inventory_by_sku": {
        Role.ADMIN,
        Role.PRODUCTION_MANAGER,
        Role.SALES,
        Role.WAREHOUSE,
        Role.PURCHASE,
    },
    "query_work_order": {Role.ADMIN, Role.PRODUCTION_MANAGER},
    "query_purchase_arrival": {
        Role.ADMIN,
        Role.PRODUCTION_MANAGER,
        Role.SALES,
        Role.WAREHOUSE,
        Role.PURCHASE,
    },
    "query_exception_sop": {
        Role.ADMIN,
        Role.PRODUCTION_MANAGER,
        Role.SALES,
        Role.WAREHOUSE,
        Role.PURCHASE,
        Role.NORMAL_USER,
    },
    "analyze_order_delivery_risk": {
        Role.ADMIN,
        Role.PRODUCTION_MANAGER,
        Role.SALES,
        Role.WAREHOUSE,
        Role.PURCHASE,
    },
    "analyze_work_order_readiness": {Role.ADMIN, Role.PRODUCTION_MANAGER},
    "analyze_purchase_delay_impact": {
        Role.ADMIN,
        Role.PRODUCTION_MANAGER,
        Role.SALES,
        Role.PURCHASE,
    },
}


def is_tool_allowed(role: str, tool_name: str) -> bool:
    return role in TOOL_PERMISSIONS.get(tool_name, set())


def is_admin(role: str) -> bool:
    return role == Role.ADMIN
