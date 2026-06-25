from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.auth import UserPermissionGrant
from app.models.permission_request import PermissionRequest
from app.services.audit_service import create_tool_call_log
from app.services.auth_service import ensure_permission, has_permission, permission_exists
from app.services.permission_change_service import create_permission_change_log


ADMIN_PERMISSION_REQUEST_API = "api:admin-permission-requests"


def _ensure_admin_permission_request_api(
    db: Session,
    admin_username: str,
    admin_role: str,
    action: str,
    request_id: int | None = None,
) -> None:
    if has_permission(db, admin_username, ADMIN_PERMISSION_REQUEST_API):
        return
    create_tool_call_log(
        db=db,
        username=admin_username,
        role=admin_role,
        tool_name="platform_permission_approval",
        tool_args={
            "action": action,
            "request_id": request_id,
            "required_permission": ADMIN_PERMISSION_REQUEST_API,
        },
        permission_allowed=False,
        success=False,
        error_message="Permission denied.",
    )
    ensure_permission(db, admin_username, ADMIN_PERMISSION_REQUEST_API)


def _to_dict(row: PermissionRequest) -> dict[str, Any]:
    return {
        "id": row.id,
        "requester_username": row.requester_username,
        "requested_permission": row.requested_permission,
        "requested_role": row.requested_role,
        "reason": row.reason,
        "status": row.status,
        "approver_username": row.approver_username,
        "approval_comment": row.approval_comment,
        "created_at": row.created_at,
        "decided_at": row.decided_at,
    }


def create_permission_request(
    db: Session,
    username: str,
    role: str,
    requested_permission: str,
    reason: str,
    requested_role: str | None = None,
) -> dict[str, Any]:
    if not permission_exists(db, requested_permission):
        raise HTTPException(status_code=404, detail="Requested permission not found.")
    row = PermissionRequest(
        requester_username=username,
        requested_permission=requested_permission,
        requested_role=requested_role,
        reason=reason,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    create_tool_call_log(
        db=db,
        username=username,
        role=role,
        tool_name="platform_permission_request",
        tool_args={
            "request_id": row.id,
            "requested_permission": requested_permission,
            "requested_role": requested_role,
        },
        permission_allowed=True,
        success=True,
        result_summary="permission request submitted",
    )
    return _to_dict(row)


def list_my_permission_requests(db: Session, username: str) -> list[dict[str, Any]]:
    rows = db.scalars(
        select(PermissionRequest)
        .where(PermissionRequest.requester_username == username)
        .order_by(PermissionRequest.id.desc())
    ).all()
    return [_to_dict(row) for row in rows]


def list_admin_permission_requests(
    db: Session, admin_username: str, admin_role: str, status: str | None = None
) -> list[dict[str, Any]]:
    _ensure_admin_permission_request_api(
        db=db,
        admin_username=admin_username,
        admin_role=admin_role,
        action="list_permission_requests",
    )
    query = select(PermissionRequest).order_by(PermissionRequest.id.desc())
    if status and status != "all":
        query = query.where(PermissionRequest.status == status)
    rows = db.scalars(query).all()
    return [_to_dict(row) for row in rows]


def approve_permission_request(
    db: Session,
    admin_username: str,
    admin_role: str,
    request_id: int,
    approval_comment: str | None = None,
) -> dict[str, Any]:
    _ensure_admin_permission_request_api(
        db=db,
        admin_username=admin_username,
        admin_role=admin_role,
        action="approve_permission_request",
        request_id=request_id,
    )
    row = db.get(PermissionRequest, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Permission request not found.")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail="Permission request already decided.")
    if not (approval_comment or "").strip():
        raise HTTPException(status_code=422, detail="Approval reason is required.")

    existing_grant = db.scalar(
        select(UserPermissionGrant).where(
            UserPermissionGrant.username == row.requester_username,
            UserPermissionGrant.permission_code == row.requested_permission,
        )
    )
    if existing_grant is None:
        db.add(
            UserPermissionGrant(
                username=row.requester_username,
                permission_code=row.requested_permission,
                granted_by=admin_username,
            )
        )
    before_allowed = existing_grant is not None

    row.status = "approved"
    row.approver_username = admin_username
    row.approval_comment = approval_comment.strip() if approval_comment else None
    row.decided_at = datetime.utcnow()
    db.add(row)
    create_permission_change_log(
        db,
        source="request_approval",
        operator_username=admin_username,
        target_type="user",
        target_identifier=row.requester_username,
        permission_code=row.requested_permission,
        before_value={"granted": before_allowed},
        after_value={"granted": True},
        diff={
            "decision": "approved",
            "granted": not before_allowed,
        },
        remark=row.approval_comment or "",
        request_id=row.id,
    )
    db.commit()
    db.refresh(row)
    create_tool_call_log(
        db=db,
        username=admin_username,
        role=admin_role,
        tool_name="platform_permission_approval",
        tool_args={
            "request_id": row.id,
            "decision": "approved",
            "requested_permission": row.requested_permission,
            "requester_username": row.requester_username,
        },
        permission_allowed=True,
        success=True,
        result_summary="permission request approved",
    )
    return _to_dict(row)


def reject_permission_request(
    db: Session,
    admin_username: str,
    admin_role: str,
    request_id: int,
    approval_comment: str | None = None,
) -> dict[str, Any]:
    _ensure_admin_permission_request_api(
        db=db,
        admin_username=admin_username,
        admin_role=admin_role,
        action="reject_permission_request",
        request_id=request_id,
    )
    row = db.get(PermissionRequest, request_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Permission request not found.")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail="Permission request already decided.")
    if not (approval_comment or "").strip():
        raise HTTPException(status_code=422, detail="Approval reason is required.")

    row.status = "rejected"
    row.approver_username = admin_username
    row.approval_comment = approval_comment.strip() if approval_comment else None
    row.decided_at = datetime.utcnow()
    db.add(row)
    create_permission_change_log(
        db,
        source="request_approval",
        operator_username=admin_username,
        target_type="user",
        target_identifier=row.requester_username,
        permission_code=row.requested_permission,
        before_value={"granted": False},
        after_value={"granted": False},
        diff={"decision": "rejected", "granted": False},
        remark=row.approval_comment or "",
        request_id=row.id,
    )
    db.commit()
    db.refresh(row)
    create_tool_call_log(
        db=db,
        username=admin_username,
        role=admin_role,
        tool_name="platform_permission_approval",
        tool_args={
            "request_id": row.id,
            "decision": "rejected",
            "requested_permission": row.requested_permission,
            "requester_username": row.requester_username,
        },
        permission_allowed=True,
        success=True,
        result_summary="permission request rejected",
    )
    return _to_dict(row)
