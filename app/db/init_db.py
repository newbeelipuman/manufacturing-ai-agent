from sqlalchemy import inspect, text

from app.db.base import Base
from app.db.session import engine
from app import models  # noqa: F401


def _ensure_compatible_schema() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())

    def add_column_if_missing(table_name: str, column_name: str, ddl: str) -> None:
        if table_name not in table_names:
            return
        columns = {column["name"] for column in inspector.get_columns(table_name)}
        if column_name in columns:
            return
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}"))

    add_column_if_missing("tool_call_log", "username", "username VARCHAR(64)")
    add_column_if_missing("tool_call_log", "request_id", "request_id VARCHAR(64)")
    add_column_if_missing("agent_call_log", "request_id", "request_id VARCHAR(64)")
    add_column_if_missing("agent_call_log", "intent", "intent VARCHAR(128)")
    add_column_if_missing("agent_call_log", "risk_level", "risk_level VARCHAR(32)")
    add_column_if_missing("agent_call_log", "response_json", "response_json JSON")
    add_column_if_missing(
        "inventory_sku",
        "quality_hold_quantity",
        "quality_hold_quantity NUMERIC(14, 2) DEFAULT 0",
    )
    add_column_if_missing(
        "inventory_batch",
        "quality_hold_quantity",
        "quality_hold_quantity NUMERIC(14, 2) DEFAULT 0",
    )
    add_column_if_missing(
        "work_order",
        "expected_replenishment_date",
        "expected_replenishment_date DATE",
    )
    add_column_if_missing("permission_change_log", "request_id", "request_id INTEGER")


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    _ensure_compatible_schema()


if __name__ == "__main__":
    init_db()
