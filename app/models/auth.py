from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuthUser(Base):
    __tablename__ = "auth_user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(128))
    password_hash: Mapped[str] = mapped_column(String(128))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class Role(Base):
    __tablename__ = "auth_role"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Permission(Base):
    __tablename__ = "auth_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    category: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class UserRole(Base):
    __tablename__ = "auth_user_role"
    __table_args__ = (UniqueConstraint("username", "role_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(64), ForeignKey("auth_user.username"), index=True
    )
    role_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("auth_role.code"), index=True
    )


class RolePermission(Base):
    __tablename__ = "auth_role_permission"
    __table_args__ = (UniqueConstraint("role_code", "permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    role_code: Mapped[str] = mapped_column(
        String(64), ForeignKey("auth_role.code"), index=True
    )
    permission_code: Mapped[str] = mapped_column(
        String(128), ForeignKey("auth_permission.code"), index=True
    )


class UserPermissionGrant(Base):
    __tablename__ = "auth_user_permission_grant"
    __table_args__ = (UniqueConstraint("username", "permission_code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(
        String(64), ForeignKey("auth_user.username"), index=True
    )
    permission_code: Mapped[str] = mapped_column(
        String(128), ForeignKey("auth_permission.code"), index=True
    )
    granted_by: Mapped[str] = mapped_column(String(64), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class MenuPermission(Base):
    __tablename__ = "auth_menu_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    menu_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(128))
    permission_code: Mapped[str] = mapped_column(
        String(128), ForeignKey("auth_permission.code"), index=True
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=100)


class ApiPermission(Base):
    __tablename__ = "auth_api_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    method: Mapped[str] = mapped_column(String(16))
    path: Mapped[str] = mapped_column(String(160), index=True)
    permission_code: Mapped[str] = mapped_column(
        String(128), ForeignKey("auth_permission.code"), index=True
    )


class DocumentPermission(Base):
    __tablename__ = "auth_document_permission"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_scope: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    permission_code: Mapped[str] = mapped_column(
        String(128), ForeignKey("auth_permission.code"), index=True
    )
