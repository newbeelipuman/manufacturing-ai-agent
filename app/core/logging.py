import logging
import sys

from app.core.config import settings


class ContextDefaultsFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        for field in ["path", "request_id", "role", "tool_name", "success", "latency_ms"]:
            if not hasattr(record, field):
                setattr(record, field, "-")
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextDefaultsFilter())
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s "
            "path=%(path)s request_id=%(request_id)s role=%(role)s tool_name=%(tool_name)s "
            "success=%(success)s latency_ms=%(latency_ms)s message=%(message)s"
        )
    )
    logging.basicConfig(
        level=settings.log_level.upper(),
        handlers=[handler],
        force=True,
    )


def log_extra(
    *,
    path: str = "-",
    request_id: str = "-",
    role: str = "-",
    tool_name: str = "-",
    success: object = "-",
    latency_ms: object = "-",
) -> dict[str, object]:
    return {
        "path": path,
        "request_id": request_id,
        "role": role,
        "tool_name": tool_name,
        "success": success,
        "latency_ms": latency_ms,
    }
