from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.permissions import is_admin
from app.db.session import get_db
from app.services.auth_service import ensure_permission, has_permission, resolve_identity
from app.services.deployment_service import (
    get_deployment_logs,
    get_deployment_report,
    get_deployment_status,
)


router = APIRouter(prefix="/api/admin/deployment", tags=["deployment"])

DEPLOYMENT_ADMIN_PERMISSION = "api:admin-deployment-status"


def _require_deployment_admin(db: Session, request: Request) -> dict[str, str]:
    identity = resolve_identity(request)
    if not is_admin(identity["role"]):
        raise HTTPException(status_code=403, detail="Only admin can access deployment APIs.")
    if not has_permission(db, identity["username"], "menu:deployment-status"):
        ensure_permission(db, identity["username"], DEPLOYMENT_ADMIN_PERMISSION)
    return identity


@router.get("/status")
def deployment_status(
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_deployment_admin(db, request)
    return get_deployment_status()


@router.get("/logs/{service}")
def deployment_logs(
    service: str,
    request: Request,
    tail: int = Query(120, ge=20, le=300),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_deployment_admin(db, request)
    return get_deployment_logs(service=service, tail=tail)


@router.get("/reports/{report_id}")
def deployment_report(
    report_id: str,
    request: Request,
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    _require_deployment_admin(db, request)
    return get_deployment_report(report_id)
