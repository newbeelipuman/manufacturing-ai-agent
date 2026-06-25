from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.permissions import is_admin, is_tool_allowed
from app.db.session import get_db
from app.schemas import GenericResponse, KnowledgeSearchResponse
from app.services.audit_service import create_tool_call_log
from app.services.auth_service import ensure_permission, has_permission, resolve_identity
from app.services.knowledge_service import rebuild_knowledge, search_knowledge

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post(
    "/rebuild",
    response_model=GenericResponse,
    summary="Rebuild simulated SOP knowledge chunks",
)
def rebuild_knowledge_endpoint(
    request: Request,
    role: str | None = Query(None),
    db: Session = Depends(get_db),
) -> GenericResponse:
    identity = resolve_identity(request, fallback_role=role)
    if not is_admin(identity["role"]):
        raise HTTPException(status_code=403, detail="Only admin can rebuild knowledge.")
    ensure_permission(db, identity["username"], "api:knowledge-rebuild")
    result = rebuild_knowledge(db)
    return GenericResponse(success=True, message="Knowledge base rebuilt.", data=result)


@router.get(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Search public SOP knowledge",
)
def search_knowledge_endpoint(
    request: Request,
    query: str = Query(..., min_length=1),
    role: str = "normal_user",
    db: Session = Depends(get_db),
) -> KnowledgeSearchResponse:
    identity = resolve_identity(request, fallback_role=role)
    role = identity["role"]
    allowed = is_tool_allowed(role, "query_exception_sop")
    if not allowed:
        message = f"Role {role} is not allowed to search SOP knowledge."
        create_tool_call_log(
            db=db,
            username=identity["username"],
            role=role,
            tool_name="query_exception_sop",
            tool_args={"query": query, "source": "/api/knowledge/search"},
            permission_allowed=False,
            success=False,
            error_message=message,
        )
        return KnowledgeSearchResponse(
            success=False,
            permission_allowed=False,
            query=query,
            results=[],
            message=message,
        )

    if not has_permission(db, identity["username"], "document:sop-public"):
        create_tool_call_log(
            db=db,
            username=identity["username"],
            role=role,
            tool_name="query_exception_sop",
            tool_args={
                "query": query,
                "source": "/api/knowledge/search",
                "required_permission": "document:sop-public",
            },
            permission_allowed=False,
            success=False,
            error_message="Permission denied.",
        )
        ensure_permission(db, identity["username"], "document:sop-public")

    results = search_knowledge(db, query=query)
    return KnowledgeSearchResponse(
        success=True,
        permission_allowed=True,
        query=query,
        results=results,
        message="Knowledge search completed.",
    )
