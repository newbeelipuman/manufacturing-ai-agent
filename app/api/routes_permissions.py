from typing import Any

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.permissions import is_admin
from app.db.session import get_db
from app.services.auth_service import resolve_identity
from app.services.permission_request_service import (
    approve_permission_request,
    create_permission_request,
    list_admin_permission_requests,
    list_my_permission_requests,
    reject_permission_request,
)
from app.services.permission_change_service import (
    get_role_permissions,
    list_permission_change_logs,
    save_role_permissions,
)

router = APIRouter(prefix="/api", tags=["permissions"])


class PermissionRequestCreate(BaseModel):
    requested_permission: str
    reason: str
    requested_role: str | None = None


class PermissionDecisionRequest(BaseModel):
    approval_comment: str | None = None


class RolePermissionSaveRequest(BaseModel):
    permission_codes: list[str]
    remark: str


@router.post("/permissions/requests")
def submit_permission_request(
    payload: PermissionRequestCreate,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    data = create_permission_request(
        db=db,
        username=identity["username"],
        role=identity["role"],
        requested_permission=payload.requested_permission,
        requested_role=payload.requested_role,
        reason=payload.reason,
    )
    return {"success": True, "data": data}


@router.get("/permissions/requests/my")
def my_permission_requests(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    return {
        "success": True,
        "data": list_my_permission_requests(db, identity["username"]),
    }


@router.get("/admin/permission-requests")
def admin_permission_requests(
    request: Request,
    status: str | None = Query(None),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="仅 admin 角色可以访问管理接口。")
    return {
        "success": True,
        "data": list_admin_permission_requests(
            db, identity["username"], identity["role"], status=status
        ),
    }


@router.post("/admin/permission-requests/{request_id}/approve")
def approve_permission_request_endpoint(
    request_id: int,
    payload: PermissionDecisionRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="仅 admin 角色可以访问管理接口。")
    data = approve_permission_request(
        db=db,
        admin_username=identity["username"],
        admin_role=identity["role"],
        request_id=request_id,
        approval_comment=payload.approval_comment,
    )
    return {"success": True, "data": data}


@router.post("/admin/permission-requests/{request_id}/reject")
def reject_permission_request_endpoint(
    request_id: int,
    payload: PermissionDecisionRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="仅 admin 角色可以访问管理接口。")
    data = reject_permission_request(
        db=db,
        admin_username=identity["username"],
        admin_role=identity["role"],
        request_id=request_id,
        approval_comment=payload.approval_comment,
    )
    return {"success": True, "data": data}


@router.get("/admin/permission-change-logs")
def admin_permission_change_logs(
    request: Request,
    source: str | None = Query(None),
    operator_username: str | None = Query(None),
    target_type: str | None = Query(None),
    target_identifier: str | None = Query(None),
    permission_code: str | None = Query(None),
    request_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Only admin can access admin APIs.")
    return {
        "success": True,
        "data": list_permission_change_logs(
            db,
            limit=limit,
            source=source,
            operator_username=operator_username,
            target_type=target_type,
            target_identifier=target_identifier,
            permission_code=permission_code,
            request_id=request_id,
        ),
    }


@router.get("/admin/role-permissions/{role_code}")
def admin_get_role_permissions(
    role_code: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Only admin can access admin APIs.")
    return {"success": True, "data": get_role_permissions(db, role_code)}


@router.post("/admin/role-permissions/{role_code}")
def admin_save_role_permissions(
    role_code: str,
    payload: RolePermissionSaveRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Only admin can access admin APIs.")
    data = save_role_permissions(
        db=db,
        admin_username=identity["username"],
        admin_role=identity["role"],
        role_code=role_code,
        permission_codes=payload.permission_codes,
        remark=payload.remark,
    )
    return {"success": True, "data": data}
