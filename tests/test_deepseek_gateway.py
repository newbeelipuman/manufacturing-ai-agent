from app.services import llm_gateway_service


def test_deepseek_gateway_uses_api_usage(monkeypatch) -> None:
    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "usage": {
                    "prompt_tokens": 11,
                    "completion_tokens": 7,
                    "total_tokens": 18,
                }
            }

    calls: list[dict] = []

    def fake_post(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return FakeResponse()

    monkeypatch.setattr(llm_gateway_service.settings, "llm_gateway_mode", "deepseek")
    monkeypatch.setattr(llm_gateway_service.settings, "llm_provider", "deepseek")
    monkeypatch.setattr(llm_gateway_service.settings, "llm_model", "deepseek-chat")
    monkeypatch.setattr(llm_gateway_service.settings, "deepseek_api_key", "test-key")
    monkeypatch.setattr(llm_gateway_service.httpx, "post", fake_post)

    route = llm_gateway_service.route_llm_request(
        question="订单 O1001 现在能不能发货？",
        intent="order_delivery_risk",
        role="sales",
    )

    assert route["provider"] == "deepseek"
    assert route["model"] == "deepseek-chat"
    assert route["prompt_tokens"] == 11
    assert route["completion_tokens"] == 7
    assert route["total_tokens"] == 18
    assert route["used_fallback"] is False
    assert calls
    assert calls[0]["kwargs"]["headers"]["Authorization"] == "Bearer test-key"


def test_deepseek_gateway_falls_back_without_key(monkeypatch) -> None:
    monkeypatch.setattr(llm_gateway_service.settings, "llm_gateway_mode", "deepseek")
    monkeypatch.setattr(llm_gateway_service.settings, "llm_provider", "deepseek")
    monkeypatch.setattr(llm_gateway_service.settings, "llm_model", "deepseek-chat")
    monkeypatch.setattr(llm_gateway_service.settings, "deepseek_api_key", "")

    route = llm_gateway_service.route_llm_request(
        question="订单 O1001 现在能不能发货？",
        intent="order_delivery_risk",
        role="sales",
    )

    assert route["provider"] == "deepseek"
    assert route["used_fallback"] is True
    assert route["error_message"] == "deepseek_api_key_missing"
