from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import (
    authenticate_user,
    create_access_token,
    get_primary_role,
    get_token_identity,
    get_user_menus,
    get_user_permissions,
)

router = APIRouter(prefix="/api", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/auth/login")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> dict[str, Any]:
    user = authenticate_user(db, request.username, request.password)
    if user is None:
        raise HTTPException(status_code=401, detail="用户名或密码错误。")
    role = get_primary_role(db, user.username)
    if role is None:
        raise HTTPException(status_code=403, detail="用户未绑定角色。")
    token = create_access_token(username=user.username, role=role)
    return {
        "success": True,
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user.username,
            "display_name": user.display_name,
            "role": role,
        },
    }


@router.get("/auth/me")
def me(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    identity = get_token_identity(request)
    if identity is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return {
        "success": True,
        "user": identity,
        "permissions": get_user_permissions(db, identity["username"]),
    }


@router.get("/auth/permissions")
def permissions(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    identity = get_token_identity(request)
    if identity is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return {
        "success": True,
        "username": identity["username"],
        "role": identity["role"],
        "permissions": get_user_permissions(db, identity["username"]),
    }


@router.get("/menus")
def menus(request: Request, db: Session = Depends(get_db)) -> dict[str, Any]:
    identity = get_token_identity(request)
    if identity is None:
        raise HTTPException(status_code=401, detail="Authentication required.")
    return {
        "success": True,
        "username": identity["username"],
        "role": identity["role"],
        "menus": get_user_menus(db, identity["username"]),
    }
