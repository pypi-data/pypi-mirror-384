"""
Lightweight LLM provider abstraction for SemFire detectors.

Default behavior attempts to use provider settings from environment variables
and an optional config file. Providers supported:
 - OpenAI (via `openai` library)
 - Gemini (via Google Generative Language REST API)
 - OpenRouter (via HTTPS REST API)
 - Perplexity (via HTTPS REST API)
 - Transformers (local/HF models via `transformers`)

Configuration resolution order:
1) Environment variable `SEMFIRE_CONFIG` pointing to a JSON config file.
2) Default user path: `~/.semfire/config.json`.

Config schema (JSON):
{
  "provider": "openai" | "gemini" | "openrouter" | "perplexity" | "transformers" | "none",
  "openai": { "api_key_env": "OPENAI_API_KEY", "base_url": null, "model": "gpt-4o-mini" },
  "gemini": { "api_key_env": "GEMINI_API_KEY", "model": "gemini-1.5-flash-latest" },
  "openrouter": { "api_key_env": "OPENROUTER_API_KEY", "model": "deepseek/deepseek-chat" },
  "perplexity": { "api_key_env": "PERPLEXITY_API_KEY", "model": "sonar-medium-online" },
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
import requests


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
    if provider == "gemini":
        gc = cfg.get("gemini", {})
        return f"provider=gemini model={gc.get('model','?')} api_key_env={gc.get('api_key_env','GEMINI_API_KEY')}"
    if provider == "openrouter":
        oc = cfg.get("openrouter", {})
        return f"provider=openrouter model={oc.get('model','?')} api_key_env={oc.get('api_key_env','OPENROUTER_API_KEY')}"
    if provider == "perplexity":
        pc = cfg.get("perplexity", {})
        return f"provider=perplexity model={pc.get('model','?')} api_key_env={pc.get('api_key_env','PERPLEXITY_API_KEY')}"
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


@dataclass
class GeminiProvider(LLMProviderBase):
    model: str
    api_key: str

    def is_ready(self) -> bool:
        return bool(self.api_key and self.model)

    def generate(self, prompt: str) -> str:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [
                    {"role": "user", "parts": [{"text": prompt}]}
                ],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 256},
            }
            resp = requests.post(url, json=payload, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates") or []
            if candidates:
                parts = (candidates[0].get("content") or {}).get("parts") or []
                if parts and isinstance(parts[0], dict):
                    return parts[0].get("text", "")
            return data.get("text", "") or ""
        except Exception as e:
            raise RuntimeError(f"Gemini generate failed: {e}")


@dataclass
class OpenRouterProvider(LLMProviderBase):
    model: str
    api_key: str

    def is_ready(self) -> bool:
        return bool(self.api_key and self.model)

    def generate(self, prompt: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful analysis model."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 256,
            }
            r = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if choices:
                msg = (choices[0].get("message") or {}).get("content")
                return msg or ""
            return ""
        except Exception as e:
            raise RuntimeError(f"OpenRouter generate failed: {e}")


@dataclass
class PerplexityProvider(LLMProviderBase):
    model: str
    api_key: str

    def is_ready(self) -> bool:
        return bool(self.api_key and self.model)

    def generate(self, prompt: str) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful analysis model."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "max_tokens": 256,
            }
            r = requests.post("https://api.perplexity.ai/chat/completions", headers=headers, json=payload, timeout=20)
            r.raise_for_status()
            data = r.json()
            choices = data.get("choices") or []
            if choices:
                msg = (choices[0].get("message") or {}).get("content")
                return msg or ""
            return ""
        except Exception as e:
            raise RuntimeError(f"Perplexity generate failed: {e}")



@dataclass
class TransformersProvider(LLMProviderBase):
    """Local/Hugging Face transformers provider.

    Loads a causal LM and tokenizer using `transformers` and generates text locally.

    Configuration
    - model_path: HF model ID (e.g., "TinyLlama/TinyLlama-1.1B-Chat-v1.0") or local path
    - device: "cpu" or "cuda" (defaults to cpu; falls back if unavailable)

    Notes
    - No API key is required for local paths. A HF token may be needed if
      downloading from the Hub, using private models, or gated weights.
    - Models are loaded lazily on first `generate()` to avoid import overhead.
    """
    model_path: str
    device: str = "cpu"

    def __post_init__(self) -> None:
        self._transformers = None  # type: ignore
        self._torch = None  # type: ignore
        self._tokenizer = None  # type: ignore
        self._model = None  # type: ignore
        # Defer heavy imports to runtime
        try:
            import transformers  # type: ignore
            import torch  # type: ignore
            self._transformers = transformers
            self._torch = torch
        except Exception:
            # Leave libs as None; is_ready() will reflect this
            pass

    def _resolve_device(self) -> str:
        if not self._torch:
            return "cpu"
        if self.device.startswith("cuda") and self._torch.cuda.is_available():
            return "cuda"
        return "cpu"

    def _ensure_loaded(self) -> None:
        if self._model is not None and self._tokenizer is not None:
            return
        if not self._transformers or not self._torch:
            raise RuntimeError("transformers/torch not available; install dependencies.")
        AutoTokenizer = self._transformers.AutoTokenizer
        AutoModelForCausalLM = self._transformers.AutoModelForCausalLM

        local_files_only = False
        # If the path exists locally, avoid network fetches
        try:
            if os.path.exists(self.model_path):
                local_files_only = True
        except Exception:
            pass

        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_path,
                local_files_only=local_files_only,
            )
            self._model = AutoModelForCausalLM.from_pretrained(
                self.model_path,
                local_files_only=local_files_only,
            )
            target = self._resolve_device()
            self._model.to(target)
            self._model.eval()
        except Exception as e:
            raise RuntimeError(f"Failed to load transformers model/tokenizer: {e}")

    def is_ready(self) -> bool:
        # Ready if deps importable and a model identifier/path is provided.
        return bool(self._transformers and self._torch and self.model_path)

    def generate(self, prompt: str) -> str:
        try:
            self._ensure_loaded()
            torch = self._torch
            tok = self._tokenizer
            mdl = self._model
            inputs = tok(prompt, return_tensors="pt")
            # Move inputs to model device
            device = next(mdl.parameters()).device
            for k in inputs:
                if hasattr(inputs[k], "to"):
                    inputs[k] = inputs[k].to(device)
            with torch.no_grad():
                output_ids = mdl.generate(
                    **inputs,
                    max_new_tokens=256,
                    do_sample=True,
                    temperature=0.2,
                    top_k=50,
                    pad_token_id=getattr(tok, "pad_token_id", None) or getattr(tok, "eos_token_id", None),
                )
            # Return only the generated continuation
            text = tok.decode(output_ids[0], skip_special_tokens=True)
            return text or ""
        except Exception as e:
            raise RuntimeError(f"Transformers generate failed: {e}")



def load_llm_provider_from_config() -> Optional[LLMProviderBase]:
    # Load ~/.semfire/.env into process first
    _load_env_file_into_process()
    cfg = _read_config()
    # Priority: explicit env var provider → config file provider → auto-detect from keys
    provider = (os.environ.get("SEMFIRE_LLM_PROVIDER") or cfg.get("provider") or "").lower()
    if not provider:
        # Auto-detect provider from present API keys (priority order)
        if os.environ.get("OPENAI_API_KEY"):
            provider = "openai"
        elif os.environ.get("GEMINI_API_KEY"):
            provider = "gemini"
        elif os.environ.get("OPENROUTER_API_KEY"):
            provider = "openrouter"
        elif os.environ.get("PERPLEXITY_API_KEY"):
            provider = "perplexity"
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
    if provider == "gemini":
        gc = cfg.get("gemini", {})
        api_key_env = gc.get("api_key_env") or "GEMINI_API_KEY"
        api_key = os.environ.get(api_key_env)
        model = gc.get("model") or os.environ.get("SEMFIRE_GEMINI_MODEL") or "gemini-1.5-flash-latest"
        if api_key and model:
            return GeminiProvider(model=model, api_key=api_key)
        return None
    if provider == "openrouter":
        oc = cfg.get("openrouter", {})
        api_key_env = oc.get("api_key_env") or "OPENROUTER_API_KEY"
        api_key = os.environ.get(api_key_env)
        model = oc.get("model") or os.environ.get("SEMFIRE_OPENROUTER_MODEL") or "deepseek/deepseek-chat"
        if api_key and model:
            return OpenRouterProvider(model=model, api_key=api_key)
        return None
    if provider == "perplexity":
        pc = cfg.get("perplexity", {})
        api_key_env = pc.get("api_key_env") or "PERPLEXITY_API_KEY"
        api_key = os.environ.get(api_key_env)
        model = pc.get("model") or os.environ.get("SEMFIRE_PERPLEXITY_MODEL") or "sonar-medium-online"
        if api_key and model:
            return PerplexityProvider(model=model, api_key=api_key)
        return None
    if provider == "transformers":
        tc = cfg.get("transformers", {})
        model_path = tc.get("model_path") or os.environ.get("SEMFIRE_TRANSFORMERS_MODEL_PATH")
        device = tc.get("device") or os.environ.get("SEMFIRE_TRANSFORMERS_DEVICE") or "cpu"
        if model_path:
            return TransformersProvider(model_path=model_path, device=device)
        return None
    return None


def write_config(provider: str,
                 openai_model: Optional[str] = None,
                 openai_api_key_env: Optional[str] = None,
                 openai_base_url: Optional[str] = None,
                 gemini_model: Optional[str] = None,
                 gemini_api_key_env: Optional[str] = None,
                 openrouter_model: Optional[str] = None,
                 openrouter_api_key_env: Optional[str] = None,
                 perplexity_model: Optional[str] = None,
                 perplexity_api_key_env: Optional[str] = None,
                 transformers_model_path: Optional[str] = None,
                 transformers_device: Optional[str] = None) -> str:
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
    elif provider == "gemini":
        cfg["gemini"] = {
            "model": gemini_model or "gemini-1.5-flash-latest",
            "api_key_env": gemini_api_key_env or "GEMINI_API_KEY",
        }
    elif provider == "openrouter":
        cfg["openrouter"] = {
            "model": openrouter_model or "deepseek/deepseek-chat",
            "api_key_env": openrouter_api_key_env or "OPENROUTER_API_KEY",
        }
    elif provider == "perplexity":
        cfg["perplexity"] = {
            "model": perplexity_model or "sonar-medium-online",
            "api_key_env": perplexity_api_key_env or "PERPLEXITY_API_KEY",
        }
    elif provider == "transformers":
        cfg["transformers"] = {
            "model_path": transformers_model_path or "",
            "device": transformers_device or "cpu",
        }
    path = os.environ.get(CONFIG_ENV, DEFAULT_CONFIG_PATH)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        return path
    except Exception:
        # Fallback to a workspace-local config if home directory is not writable (e.g., sandboxed tests)
        fallback = os.path.join(os.getcwd(), ".semfire", "config.json")
        os.makedirs(os.path.dirname(fallback), exist_ok=True)
        with open(fallback, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        # Ensure subsequent reads use the fallback path
        os.environ[CONFIG_ENV] = fallback
        return fallback
