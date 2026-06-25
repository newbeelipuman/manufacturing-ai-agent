from datetime import datetime
import logging
from uuid import uuid4

from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routes_admin import router as admin_router
from app.api.routes_auth import router as auth_router
from app.api.routes_chat import router as chat_router
from app.api.routes_deployment import router as deployment_router
from app.api.routes_health import router as health_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_permissions import router as permissions_router
from app.api.routes_tools import router as tools_router
from app.core.config import settings
from app.core.logging import configure_logging, log_extra
from app.core.request_context import reset_request_id, set_request_id


def _json_safe_error_detail(value):
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {key: _json_safe_error_detail(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe_error_detail(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe_error_detail(item) for item in value]
    return value


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title=settings.app_name,
        description="Manufacturing ERP/MES/WMS business query Agent MVP.",
        version=settings.app_version,
    )

    @app.middleware("http")
    async def structured_request_log(request: Request, call_next):
        started_at = datetime.utcnow()
        request_id = request.headers.get("x-request-id") or str(uuid4())
        context_token = set_request_id(request_id)
        role = request.query_params.get("role", "-")
        try:
            response = await call_next(request)
            response.headers["x-request-id"] = request_id
            success = response.status_code < 400
            return response
        finally:
            latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
            logging.getLogger("app.request").info(
                "request_completed",
                extra=log_extra(
                    path=request.url.path,
                    request_id=request_id,
                    role=role,
                    success=success if "success" in locals() else False,
                    latency_ms=latency_ms,
                ),
            )
            reset_request_id(context_token)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {"code": exc.status_code, "message": exc.detail},
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "error": {
                    "code": 422,
                    "message": "请求参数校验失败。",
                    "details": _json_safe_error_detail(exc.errors()),
                },
            },
        )

    @app.exception_handler(Exception)
    async def unknown_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logging.getLogger("app.error").exception(
            "unhandled_exception",
            extra=log_extra(path=request.url.path, success=False),
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": {"code": 500, "message": "服务内部异常，请稍后重试。"},
            },
        )

    app.include_router(health_router)
    app.include_router(auth_router)
    app.include_router(chat_router)
    app.include_router(tools_router)
    app.include_router(knowledge_router)
    app.include_router(permissions_router)
    app.include_router(admin_router)
    app.include_router(deployment_router)
    return app


app = create_app()
