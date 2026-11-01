"""Run with:  cd backend && pytest -q   (no network needed - HTTP is mocked)"""
import asyncio

import pytest

from app.config import settings
from app.services import llm

GOOD_JSON = '{"description":"d","main_uses":["a"],"nutrition":null,"storage_tips":["s"],"shopping_advice":"ok"}'


def set_cfg(monkeypatch, provider, key="k", model="", base=""):
    monkeypatch.setattr(settings, "LLM_PROVIDER", provider)
    monkeypatch.setattr(settings, "LLM_API_KEY", key)
    monkeypatch.setattr(settings, "LLM_MODEL", model)
    monkeypatch.setattr(settings, "LLM_BASE_URL", base)


def test_presets_resolve(monkeypatch):
    set_cfg(monkeypatch, "gemini")
    c = llm.resolve_config()
    assert c.kind == "gemini" and c.model == "gemini-2.5-flash" and c.configured
    set_cfg(monkeypatch, "groq", model="my-model")
    assert llm.resolve_config().model == "my-model"


def test_ollama_needs_no_key(monkeypatch):
    set_cfg(monkeypatch, "ollama", key="")
    assert llm.resolve_config().configured


def test_missing_key_not_configured(monkeypatch):
    set_cfg(monkeypatch, "openai", key="")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert not llm.resolve_config().configured


def test_custom_requires_base_and_model(monkeypatch):
    set_cfg(monkeypatch, "custom", base="http://x/v1", model="m")
    assert llm.resolve_config().configured
    set_cfg(monkeypatch, "custom")
    assert not llm.resolve_config().configured


def test_parse_json_handles_fences():
    assert llm._parse_json("```json\n" + GOOD_JSON + "\n```")["description"] == "d"


def test_fallback_when_no_key(monkeypatch):
    set_cfg(monkeypatch, "openai", key="")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    ai, meta = asyncio.run(llm.generate_product_info("milk", {}, {}))
    assert meta["llm_used"] is False and ai["shopping_advice"]


class FakeResp:
    def __init__(self, data, status=200):
        self._d, self.status_code, self.text = data, status, str(data)

    def raise_for_status(self):
        pass

    def json(self):
        return self._d


@pytest.mark.parametrize("provider,payload", [
    ("anthropic", {"content": [{"type": "text", "text": GOOD_JSON}]}),
    ("gemini", {"candidates": [{"content": {"parts": [{"text": GOOD_JSON}]}}]}),
    ("openai", {"choices": [{"message": {"content": GOOD_JSON}}]}),
    ("groq", {"choices": [{"message": {"content": GOOD_JSON}}]}),
])
def test_each_wire_format(monkeypatch, provider, payload):
    set_cfg(monkeypatch, provider)
    llm._CACHE.clear()

    class FakeClient:
        def __init__(self, *a, **k): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def post(self, url, **kw): return FakeResp(payload)

    monkeypatch.setattr(llm.httpx, "AsyncClient", FakeClient)
    ai, meta = asyncio.run(llm.generate_product_info("milk", {}, {}))
    assert meta["llm_used"] and meta["provider"] == provider and ai["description"] == "d"
