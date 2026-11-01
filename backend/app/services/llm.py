"""Generative-AI service - works with ANY major LLM provider.

Pick one with LLM_PROVIDER in backend/.env:

  anthropic   Claude                       (own API format)
  openai      ChatGPT / GPT models         (OpenAI format)
  gemini      Google Gemini                (own API format)
  groq        Groq (Llama etc.)            (OpenAI-compatible)
  openrouter  OpenRouter (100+ models)     (OpenAI-compatible)
  deepseek    DeepSeek                     (OpenAI-compatible)
  mistral     Mistral                      (OpenAI-compatible)
  ollama      Local models, no key needed  (OpenAI-compatible)
  custom      Any OpenAI-compatible server (set LLM_BASE_URL + LLM_MODEL)

Only three wire formats exist ("anthropic", "gemini", "openai"), so adding a new
provider is just one more entry in PRESETS. Calls use plain HTTPS (httpx) - no vendor SDKs.
If no key is set, or the call fails, a small offline fallback keeps the UI working.
"""
import json
import os
import re
from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional

import httpx

from ..config import settings

# kind = wire format | base = API root | model = default model | key_env = provider-specific env var
PRESETS = {
    "anthropic":  {"kind": "anthropic", "base": "https://api.anthropic.com/v1",
                   "model": "claude-sonnet-5-5", "key_env": "ANTHROPIC_API_KEY"},
    "openai":     {"kind": "openai", "base": "https://api.openai.com/v1",
                   "model": "gpt-4o-mini", "key_env": "OPENAI_API_KEY"},
    "gemini":     {"kind": "gemini", "base": "https://generativelanguage.googleapis.com/v1beta",
                   "model": "gemini-2.5-flash", "key_env": "GEMINI_API_KEY"},
    "groq":       {"kind": "openai", "base": "https://api.groq.com/openai/v1",
                   "model": "llama-3.3-70b-versatile", "key_env": "GROQ_API_KEY"},
    "openrouter": {"kind": "openai", "base": "https://openrouter.ai/api/v1",
                   "model": "openai/gpt-4o-mini", "key_env": "OPENROUTER_API_KEY"},
    "deepseek":   {"kind": "openai", "base": "https://api.deepseek.com/v1",
                   "model": "deepseek-chat", "key_env": "DEEPSEEK_API_KEY"},
    "mistral":    {"kind": "openai", "base": "https://api.mistral.ai/v1",
                   "model": "mistral-small-latest", "key_env": "MISTRAL_API_KEY"},
    "ollama":     {"kind": "openai", "base": "http://localhost:11434/v1",
                   "model": "llama3.2", "key_env": "", "needs_key": False},
    "custom":     {"kind": "openai", "base": "", "model": "", "key_env": ""},
}

SYSTEM_PROMPT = (
    "You are a concise, practical smart-shopping assistant. "
    "Respond with ONLY a valid JSON object (no markdown, no commentary) with exactly these keys:\n"
    '  "description": string, 1-2 sentences about the product,\n'
    '  "main_uses": array of 3-5 short strings,\n'
    '  "nutrition": object or null. Use null if the item is not food/drink. Otherwise: '
    '{"per": "100 g" or "100 ml" or "1 medium piece", "items": [{"label": string, "value": string}], '
    '"note": string} with calories, protein, carbs, fat, and any other key nutrient. Values are approximate,\n'
    '  "storage_tips": array of 2-4 short strings,\n'
    '  "shopping_advice": string, max 2 sentences. If the product is damaged or expired/expiring, '
    "advise clearly on whether to buy it."
)

_CACHE: "OrderedDict[str, tuple]" = OrderedDict()  # tiny in-memory cache (not a database)
_CACHE_MAX = 64


# --------------------------------------------------------------------------- configuration
@dataclass
class LLMConfig:
    provider: str
    kind: str
    base_url: str
    model: str
    api_key: str
    configured: bool


def resolve_config() -> LLMConfig:
    """Merge the provider preset with .env overrides (LLM_API_KEY / LLM_MODEL / LLM_BASE_URL)."""
    provider = settings.LLM_PROVIDER
    preset = PRESETS.get(provider, PRESETS["custom"])
    # Generic LLM_API_KEY wins; otherwise fall back to the provider-specific variable.
    key = settings.LLM_API_KEY or (os.getenv(preset["key_env"], "") if preset["key_env"] else "")
    base = (settings.LLM_BASE_URL or preset["base"]).rstrip("/")
    model = settings.LLM_MODEL or preset["model"]
    needs_key = preset.get("needs_key", True)
    configured = bool(base and model and (key or not needs_key))
    return LLMConfig(provider, preset["kind"], base, model, key, configured)


def llm_status() -> dict:
    cfg = resolve_config()
    return {"llm_provider": cfg.provider, "llm_model": cfg.model, "llm_configured": cfg.configured}


# --------------------------------------------------------------------------- prompt / parsing
def _build_user_prompt(name: str, damage: dict, dates: dict) -> str:
    return json.dumps(
        {
            "product": name,
            "visible_damage": damage.get("is_damaged"),
            "damage_reasons": damage.get("reasons"),
            "manufacturing_date": dates.get("manufacturing_date"),
            "expiry_date": dates.get("expiry_date"),
            "expiry_status": dates.get("status"),
            "days_until_expiry": dates.get("days_left"),
        }
    )


def _parse_json(text: str) -> dict:
    """Extract the first JSON object from the model output (handles ```json fences)."""
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("LLM did not return JSON")
    return json.loads(text[start : end + 1])


# --------------------------------------------------------------------------- provider calls
async def _call_anthropic(cfg: LLMConfig, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(
            f"{cfg.base_url}/messages",
            headers={"x-api-key": cfg.api_key, "anthropic-version": "2023-06-01"},
            json={
                "model": cfg.model,
                "max_tokens": 900,
                "system": SYSTEM_PROMPT,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        r.raise_for_status()
        return "".join(b.get("text", "") for b in r.json()["content"])


async def _call_gemini(cfg: LLMConfig, prompt: str) -> str:
    async with httpx.AsyncClient(timeout=40) as client:
        r = await client.post(
            f"{cfg.base_url}/models/{cfg.model}:generateContent",
            headers={"x-goog-api-key": cfg.api_key},
            json={
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "maxOutputTokens": 1200},
            },
        )
        r.raise_for_status()
        parts = r.json()["candidates"][0]["content"]["parts"]
        return "".join(p.get("text", "") for p in parts)


async def _call_openai_compatible(cfg: LLMConfig, prompt: str) -> str:
    """OpenAI, Groq, OpenRouter, DeepSeek, Mistral, Ollama, LM Studio, vLLM..."""
    headers = {"Authorization": f"Bearer {cfg.api_key}"} if cfg.api_key else {}
    body = {
        "model": cfg.model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{cfg.base_url}/chat/completions", headers=headers, json=body)
        if r.status_code == 400:  # some servers/models reject response_format - retry without it
            body.pop("response_format")
            r = await client.post(f"{cfg.base_url}/chat/completions", headers=headers, json=body)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


_CALLERS = {"anthropic": _call_anthropic, "gemini": _call_gemini, "openai": _call_openai_compatible}


# --------------------------------------------------------------------------- fallback + public API
def _fallback(name: str, damage: dict, dates: dict) -> dict:
    """Generic content shown when no LLM is configured / reachable."""
    advice = "Add an LLM API key in backend/.env to get AI-generated advice."
    if damage.get("is_damaged"):
        advice = "Packaging looks damaged - choose another item or ask the store to check it."
    elif dates.get("status") == "expired":
        advice = "This item appears to be expired - do not buy it."
    elif dates.get("status") == "expiring_soon":
        advice = "This item expires soon - buy only if you will use it quickly."
    return {
        "description": f"Detected product: {name}. Configure an LLM API key for a detailed description.",
        "main_uses": ["AI-generated uses are unavailable without an API key"],
        "nutrition": None,
        "storage_tips": ["Store in a cool, dry place unless the label says otherwise."],
        "shopping_advice": advice,
    }


def _describe_error(exc: Exception) -> str:
    if isinstance(exc, httpx.HTTPStatusError):
        return f"HTTP {exc.response.status_code}: {exc.response.text[:160]}"
    return f"{type(exc).__name__}: {str(exc)[:160]}"


async def generate_product_info(name: str, damage: dict, dates: dict) -> tuple[dict, dict]:
    """Return (ai_content, meta). `meta` says whether a real LLM produced the answer."""
    cfg = resolve_config()
    if not cfg.configured:
        return _fallback(name, damage, dates), {"llm_used": False, "reason": "no_api_key", "provider": cfg.provider}

    prompt = _build_user_prompt(name, damage, dates)
    cache_key = f"{cfg.provider}|{cfg.model}|{prompt}"
    if cache_key in _CACHE:
        _CACHE.move_to_end(cache_key)
        return _CACHE[cache_key]

    try:
        raw = await _CALLERS[cfg.kind](cfg, prompt)
        out = (_parse_json(raw), {"llm_used": True, "provider": cfg.provider, "model": cfg.model})
        _CACHE[cache_key] = out
        if len(_CACHE) > _CACHE_MAX:
            _CACHE.popitem(last=False)
        return out
    except Exception as exc:  # network error, bad key, bad JSON...
        return _fallback(name, damage, dates), {
            "llm_used": False,
            "reason": "llm_error",
            "provider": cfg.provider,
            "model": cfg.model,
            "error": _describe_error(exc),
        }
