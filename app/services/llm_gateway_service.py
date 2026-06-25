from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from app.core.config import settings


def _estimate_tokens(text: str) -> int:
    return max(1, (len(text) + 3) // 4)


def route_llm_request(
    question: str,
    intent: str,
    role: str,
    provider: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Route model metadata through mock or DeepSeek without bypassing tool controls."""
    started_at = datetime.utcnow()
    selected_provider = provider or settings.llm_provider
    selected_model = model or settings.llm_model
    prompt = f"role={role}\nintent={intent}\nquestion={question}"
    prompt_tokens = _estimate_tokens(prompt)
    completion_tokens = _estimate_tokens(intent) + 8
    mode = settings.llm_gateway_mode
    if mode == "deepseek" or selected_provider == "deepseek":
        return _route_deepseek(
            started_at=started_at,
            prompt=prompt,
            prompt_tokens=prompt_tokens,
            selected_model=selected_model,
        )
    latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
    return {
        "provider": selected_provider,
        "model": selected_model,
        "fallback_model": settings.llm_fallback_model,
        "mode": mode,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
        "latency_ms": latency_ms,
        "used_fallback": False,
    }


def _route_deepseek(
    started_at: datetime,
    prompt: str,
    prompt_tokens: int,
    selected_model: str,
) -> dict[str, Any]:
    fallback = {
        "provider": "deepseek",
        "model": selected_model,
        "fallback_model": settings.llm_fallback_model,
        "mode": settings.llm_gateway_mode,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": _estimate_tokens(settings.llm_fallback_model),
        "total_tokens": prompt_tokens + _estimate_tokens(settings.llm_fallback_model),
        "latency_ms": 0,
        "used_fallback": True,
    }
    if not settings.deepseek_api_key:
        latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        return {**fallback, "latency_ms": latency_ms, "error_message": "deepseek_api_key_missing"}

    try:
        response = httpx.post(
            f"{settings.deepseek_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.deepseek_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": selected_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are only used for routing metadata in a read-only "
                            "manufacturing MVP. Do not propose business write actions."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_tokens": 16,
            },
            timeout=settings.deepseek_timeout_seconds,
        )
        response.raise_for_status()
        body = response.json()
        usage = body.get("usage", {}) if isinstance(body, dict) else {}
        actual_prompt_tokens = int(usage.get("prompt_tokens") or prompt_tokens)
        actual_completion_tokens = int(
            usage.get("completion_tokens") or _estimate_tokens(selected_model)
        )
        latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        return {
            "provider": "deepseek",
            "model": selected_model,
            "fallback_model": settings.llm_fallback_model,
            "mode": settings.llm_gateway_mode,
            "prompt_tokens": actual_prompt_tokens,
            "completion_tokens": actual_completion_tokens,
            "total_tokens": int(
                usage.get("total_tokens")
                or actual_prompt_tokens + actual_completion_tokens
            ),
            "latency_ms": latency_ms,
            "used_fallback": False,
        }
    except (httpx.HTTPError, ValueError) as exc:
        latency_ms = int((datetime.utcnow() - started_at).total_seconds() * 1000)
        return {
            **fallback,
            "latency_ms": latency_ms,
            "error_message": exc.__class__.__name__,
        }
