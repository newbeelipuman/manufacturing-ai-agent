import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas import ChatRequest, ChatResponse
from app.services.agent_service import chat
from app.services.auth_service import resolve_identity

router = APIRouter(prefix="/api", tags=["chat"])


async def _read_chat_payload(request: Request) -> ChatRequest:
    raw_body = await request.body()
    if not raw_body:
        raise HTTPException(status_code=422, detail="请求体必须是 JSON 对象。")
    try:
        data: Any = json.loads(raw_body)
        if isinstance(data, str):
            data = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail="请求体必须是 JSON 对象。") from exc
    if not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="请求体必须是 JSON 对象。")
    try:
        return ChatRequest.model_validate(data)
    except ValidationError as exc:
        raise RequestValidationError(exc.errors()) from exc


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Route a natural-language manufacturing question",
)
async def chat_endpoint(request: Request, db: Session = Depends(get_db)) -> ChatResponse:
    payload = await _read_chat_payload(request)
    identity = resolve_identity(
        request, fallback_username=payload.username, fallback_role=payload.role
    )
    return chat(
        db=db,
        username=identity["username"],
        role=identity["role"],
        question=payload.question,
    )
