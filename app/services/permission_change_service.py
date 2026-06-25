from typing import Any

from fastapi import HTTPException
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.auth import Permission, Role, RolePermission
from app.models.permission_change import PermissionChangeLog
from app.services.audit_service import create_tool_call_log
from app.services.auth_service import ensure_permission, has_permission


ADMIN_PERMISSION_CHANGE_API = "api:admin-permission-requests"


def _clean_remark(remark: str | None) -> str:
    cleaned = (remark or "").strip()
    if not cleaned:
        raise HTTPException(status_code=422, detail="Permission change remark is required.")
    return cleaned


def create_permission_change_log(
    db: Session,
    *,
    source: str,
    operator_username: str,
    target_type: str,
    target_identifier: str,
    permission_code: str | None,
    before_value: Any | None,
    after_value: Any | None,
    diff: Any | None,
    remark: str,
    request_id: int | None = None,
) -> PermissionChangeLog:
    row = PermissionChangeLog(
        source=source,
        operator_username=operator_username,
        target_type=target_type,
        target_identifier=target_identifier,
        permission_code=permission_code,
        before_value=before_value,
        after_value=after_value,
        diff=diff,
        remark=_clean_remark(remark),
        request_id=request_id,
    )
    db.add(row)
    return row


def list_permission_change_logs(
    db: Session,
    *,
    limit: int = 50,
    source: str | None = None,
    operator_username: str | None = None,
    target_type: str | None = None,
    target_identifier: str | None = None,
    permission_code: str | None = None,
    request_id: int | None = None,
) -> list[dict[str, Any]]:
    query = select(PermissionChangeLog)
    if source:
        query = query.where(PermissionChangeLog.source == source)
    if operator_username:
        query = query.where(PermissionChangeLog.operator_username == operator_username)
    if target_type:
        query = query.where(PermissionChangeLog.target_type == target_type)
    if target_identifier:
        query = query.where(PermissionChangeLog.target_identifier == target_identifier)
    if permission_code:
        query = query.where(PermissionChangeLog.permission_code == permission_code)
    if request_id is not None:
        query = query.where(PermissionChangeLog.request_id == request_id)
    rows = db.scalars(query.order_by(PermissionChangeLog.id.desc()).limit(limit)).all()
    return [
        {
            "id": row.id,
            "source": row.source,
            "operator_username": row.operator_username,
            "target_type": row.target_type,
            "target_identifier": row.target_identifier,
            "permission_code": row.permission_code,
            "before_value": row.before_value,
            "after_value": row.after_value,
            "diff": row.diff,
            "remark": row.remark,
            "request_id": row.request_id,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def get_role_permissions(db: Session, role_code: str) -> dict[str, Any]:
    role = db.scalar(select(Role).where(Role.code == role_code))
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found.")
    permissions = sorted(
        db.scalars(
            select(RolePermission.permission_code).where(RolePermission.role_code == role_code)
        ).all()
    )
    return {"role_code": role.code, "role_name": role.name, "permissions": permissions}


def save_role_permissions(
    db: Session,
    *,
    admin_username: str,
    admin_role: str,
    role_code: str,
    permission_codes: list[str],
    remark: str,
) -> dict[str, Any]:
    if not has_permission(db, admin_username, ADMIN_PERMISSION_CHANGE_API):
        create_tool_call_log(
            db=db,
            username=admin_username,
            role=admin_role,
            tool_name="platform_permission_admin_change",
            tool_args={
                "role_code": role_code,
                "source": "admin_direct_change",
                "required_permission": ADMIN_PERMISSION_CHANGE_API,
            },
            permission_allowed=False,
            success=False,
            error_message="Permission denied.",
        )
        ensure_permission(db, admin_username, ADMIN_PERMISSION_CHANGE_API)
    cleaned_remark = _clean_remark(remark)
    before = get_role_permissions(db, role_code)["permissions"]
    after = sorted(set(permission_codes))
    existing_permissions = set(
        db.scalars(select(Permission.code).where(Permission.code.in_(after))).all()
    )
    missing_permissions = sorted(set(after) - existing_permissions)
    if missing_permissions:
        raise HTTPException(
            status_code=404,
            detail=f"Permission not found: {', '.join(missing_permissions)}",
        )
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))

    db.execute(delete(RolePermission).where(RolePermission.role_code == role_code))
    for permission_code in after:
        db.add(RolePermission(role_code=role_code, permission_code=permission_code))

    log = create_permission_change_log(
        db,
        source="admin_direct_change",
        operator_username=admin_username,
        target_type="role",
        target_identifier=role_code,
        permission_code=None,
        before_value={"permissions": before},
        after_value={"permissions": after},
        diff={"added": added, "removed": removed},
        remark=cleaned_remark,
    )
    create_tool_call_log(
        db=db,
        username=admin_username,
        role=admin_role,
        tool_name="platform_permission_admin_change",
        tool_args={
            "role_code": role_code,
            "added": added,
            "removed": removed,
            "source": "admin_direct_change",
        },
        permission_allowed=True,
        success=True,
        result_summary="role permissions changed by admin",
    )
    db.commit()
    return {
        "role_code": role_code,
        "permissions": after,
        "change_log_id": log.id,
        "source": "admin_direct_change",
        "added": added,
        "removed": removed,
    }
