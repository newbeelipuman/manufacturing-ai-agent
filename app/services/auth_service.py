from __future__ import annotations

import base64
from datetime import datetime, timedelta
import hashlib
import hmac
import json
from typing import Any
from uuid import uuid4

from fastapi import HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.auth import (
    AuthUser,
    MenuPermission,
    Permission,
    RolePermission,
    UserPermissionGrant,
    UserRole,
)


DEMO_PASSWORD = "demo123456"


def hash_password(password: str) -> str:
    return hashlib.sha256(f"manufacturing-ai-agent:{password}".encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hmac.compare_digest(hash_password(password), password_hash)


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(f"{data}{padding}".encode("ascii"))


def create_access_token(username: str, role: str) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    now = datetime.utcnow()
    payload = {
        "sub": username,
        "username": username,
        "role": role,
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "iat": int(now.timestamp()),
        "jti": str(uuid4()),
    }
    signing_input = ".".join(
        [
            _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="Invalid token.") from exc

    signing_input = f"{header_part}.{payload_part}"
    expected_signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    if not hmac.compare_digest(_b64encode(expected_signature), signature_part):
        raise HTTPException(status_code=401, detail="Invalid token signature.")

    payload = json.loads(_b64decode(payload_part))
    if int(payload.get("exp", 0)) < int(datetime.utcnow().timestamp()):
        raise HTTPException(status_code=401, detail="Token expired.")
    return payload


def get_bearer_token(request: Request) -> str | None:
    auth_header = request.headers.get("authorization") or ""
    scheme, _, token = auth_header.partition(" ")
    if scheme.lower() != "bearer" or not token:
        return None
    return token


def get_token_identity(request: Request) -> dict[str, str] | None:
    token = get_bearer_token(request)
    if not token:
        return None
    payload = decode_access_token(token)
    return {
        "username": str(payload.get("username") or payload.get("sub") or ""),
        "role": str(payload.get("role") or ""),
    }


def resolve_identity(
    request: Request,
    fallback_username: str = "demo_admin",
    fallback_role: str | None = None,
) -> dict[str, str]:
    token_identity = get_token_identity(request)
    if token_identity:
        return token_identity
    if fallback_role:
        return {"username": fallback_username, "role": fallback_role}
    raise HTTPException(status_code=401, detail="Authentication required.")


def get_primary_role(db: Session, username: str) -> str | None:
    return db.scalar(
        select(UserRole.role_code).where(UserRole.username == username).limit(1)
    )


def authenticate_user(db: Session, username: str, password: str) -> AuthUser | None:
    user = db.scalar(select(AuthUser).where(AuthUser.username == username))
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_permissions(db: Session, username: str) -> list[str]:
    role_codes = list(
        db.scalars(select(UserRole.role_code).where(UserRole.username == username)).all()
    )
    permission_codes: set[str] = set()
    if role_codes:
        permission_codes.update(
            db.scalars(
                select(RolePermission.permission_code).where(
                    RolePermission.role_code.in_(role_codes)
                )
            ).all()
        )
    permission_codes.update(
        db.scalars(
            select(UserPermissionGrant.permission_code).where(
                UserPermissionGrant.username == username
            )
        ).all()
    )
    return sorted(permission_codes)


def get_user_menus(db: Session, username: str) -> list[dict[str, Any]]:
    permissions = set(get_user_permissions(db, username))
    rows = db.scalars(select(MenuPermission).order_by(MenuPermission.sort_order.asc())).all()
    return [
        {
            "key": row.menu_key,
            "label": row.label,
            "permission_code": row.permission_code,
        }
        for row in rows
        if row.permission_code in permissions
    ]


def has_permission(db: Session, username: str, permission_code: str) -> bool:
    return permission_code in set(get_user_permissions(db, username))


def ensure_permission(db: Session, username: str, permission_code: str) -> None:
    if not has_permission(db, username, permission_code):
        raise HTTPException(status_code=403, detail="Permission denied.")


def permission_exists(db: Session, code: str) -> bool:
    return db.scalar(select(Permission.id).where(Permission.code == code)) is not None
