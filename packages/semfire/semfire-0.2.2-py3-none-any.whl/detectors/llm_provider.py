"""
Lightweight LLM provider abstraction for SemFire detectors.

Default behavior attempts to use provider settings from environment variables
and an optional config file. Providers supported:
 - OpenAI (via `openai` library)

Configuration resolution order:
1) Environment variable `SEMFIRE_CONFIG` pointing to a JSON config file.
2) Default user path: `~/.semfire/config.json`.

Config schema (JSON):
{
  "provider": "openai" | "transformers" | "none",
  "openai": { "api_key_env": "OPENAI_API_KEY", "base_url": null, "model": "gpt-4o-mini" },
  "transformers": { "model_path": "/absolute/or/relative/path", "device": "cpu" }
}

Notes:
- We never persist raw API keys to disk by default; use env var indirection.
- If nothing is configured and env vars are missing, provider returns None and
  detectors fall back gracefully.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Optional, Any, Dict


CONFIG_ENV = "SEMFIRE_CONFIG"
DEFAULT_CONFIG_PATH = os.path.expanduser("~/.semfire/config.json")
ENV_FILE_PATH = os.path.expanduser("~/.semfire/.env")
LOCAL_ENV_FILE = os.path.join(os.getcwd(), ".env")


def _read_config() -> Dict[str, Any]:
    path = os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _load_env_file_into_process() -> None:
    try:
        # Load local .env first (project/cwd), then user-level ~/.semfire/.env
        def load_path(p: str):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        if "=" not in line:
                            continue
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip().strip('"').strip("'")
                        os.environ.setdefault(k, v)
            except Exception:
                pass
        if os.path.isfile(LOCAL_ENV_FILE):
            load_path(LOCAL_ENV_FILE)
        if os.path.isfile(ENV_FILE_PATH):
            load_path(ENV_FILE_PATH)
    except Exception:
        pass


def get_config_summary() -> str:
    cfg = _read_config()
    provider = cfg.get("provider", os.environ.get("SEMFIRE_LLM_PROVIDER", "none"))
    if provider == "openai":
        oc = cfg.get("openai", {})
        return f"provider=openai model={oc.get('model','?')} base_url={oc.get('base_url','default')} api_key_env={oc.get('api_key_env','OPENAI_API_KEY')}"
    if provider == "transformers":
        tc = cfg.get("transformers", {})
        return f"provider=transformers path={tc.get('model_path','?')} device={tc.get('device','cpu')}"
    env_provider = os.environ.get("SEMFIRE_LLM_PROVIDER")
    if env_provider:
        return f"provider={env_provider} (env)"
    return "provider=none"


class LLMProviderBase:
    def is_ready(self) -> bool:
        raise NotImplementedError

    def generate(self, prompt: str) -> str:
        raise NotImplementedError


@dataclass
class OpenAIProvider(LLMProviderBase):
    model: str
    api_key: str
    base_url: Optional[str] = None

    def __post_init__(self) -> None:
        try:
            import openai  # type: ignore
            self._openai = openai
            # Legacy SDK initialization (>=0.27.x). We avoid new client style to maintain compat.
            self._openai.api_key = self.api_key
            if self.base_url:
                # Some proxies/oss providers use base_url override
                setattr(self._openai, "api_base", self.base_url)
        except Exception as e:
            # Defer error to is_ready()
            self._openai = None  # type: ignore

    def is_ready(self) -> bool:
        return bool(self._openai and self.api_key and self.model)

    def generate(self, prompt: str) -> str:
        # Use ChatCompletion for broader model compatibility
        try:
            resp = self._openai.ChatCompletion.create(  # type: ignore[attr-defined]
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful analysis model."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=256,
            )
            msg = resp["choices"][0]["message"]["content"]
            return msg or ""
        except Exception as e:
            raise RuntimeError(f"OpenAI generate failed: {e}")




def load_llm_provider_from_config() -> Optional[LLMProviderBase]:
    # Load ~/.semfire/.env into process first
    _load_env_file_into_process()
    cfg = _read_config()
    # Priority: explicit env var provider → config file provider → auto-detect from keys
    provider = (os.environ.get("SEMFIRE_LLM_PROVIDER") or cfg.get("provider") or "").lower()
    if not provider:
        # Auto-detect provider from present API keys
        if os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        else:
            provider = "none"
    if provider == "openai":
        oc = cfg.get("openai", {})
        api_key_env = oc.get("api_key_env") or "OPENAI_API_KEY"
        api_key = os.environ.get(api_key_env)
        model = oc.get("model") or os.environ.get("SEMFIRE_OPENAI_MODEL") or "gpt-4o-mini"
        base_url = oc.get("base_url") or os.environ.get("OPENAI_BASE_URL")
        if api_key and model:
            return OpenAIProvider(model=model, api_key=api_key, base_url=base_url)
        return None
    return None


def write_config(provider: str,
                 openai_model: Optional[str] = None,
                 openai_api_key_env: Optional[str] = None,
                 openai_base_url: Optional[str] = None) -> str:
    """Write configuration to the resolved config path.

    Returns the path used.
    """
    cfg: Dict[str, Any] = {"provider": provider}
    if provider == "openai":
        cfg["openai"] = {
            "model": openai_model or "gpt-4o-mini",
            "api_key_env": openai_api_key_env or "OPENAI_API_KEY",
            "base_url": openai_base_url,
        }
    path = os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return path
