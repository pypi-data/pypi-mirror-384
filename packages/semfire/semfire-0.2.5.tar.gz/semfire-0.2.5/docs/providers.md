## LLM Providers & Configuration

SemFire supports multiple LLM providers behind a unified interface used by the EchoChamberDetector for optional LLM analysis. You can run without any provider; rule/heuristic analysis continues to work.

 - Supported providers: `openai`, `gemini`, `openrouter`, `perplexity`, `transformers` (local/HF models via `transformers`).
- Selection order (auto-detect): If `SEMFIRE_LLM_PROVIDER` is not set, SemFire picks the first available key in this order: `OPENAI_API_KEY` → `GEMINI_API_KEY` → `OPENROUTER_API_KEY` → `PERPLEXITY_API_KEY`. Note that the `transformers` provider is not part of this auto-detection and must be explicitly configured.
- Explicit selection: set `SEMFIRE_LLM_PROVIDER` to one of the provider names above.
- Models via env (optional):
  - OpenAI: `SEMFIRE_OPENAI_MODEL` (default `gpt-4o-mini`), optional `OPENAI_BASE_URL`.
  - Gemini: `SEMFIRE_GEMINI_MODEL` (default `gemini-1.5-flash-latest`).
  - OpenRouter: `SEMFIRE_OPENROUTER_MODEL` (default `deepseek/deepseek-chat`).
  - Perplexity: `SEMFIRE_PERPLEXITY_MODEL` (default `sonar-medium-online`).
- API keys expected in environment:
  - `OPENAI_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `PERPLEXITY_API_KEY`.

Transformers (local/HF)
- Configure via config JSON or env:
  - Config JSON (example):
    ```json
    {
      "provider": "transformers",
      "transformers": { "model_path": "TinyLlama/TinyLlama-1.1B-Chat-v1.0", "device": "cpu" }
    }
    ```
  - Env vars: `SEMFIRE_LLM_PROVIDER=transformers`, `SEMFIRE_TRANSFORMERS_MODEL_PATH=<hf-id-or-local-path>`, optional `SEMFIRE_TRANSFORMERS_DEVICE=cpu|cuda`.
- Local paths do not require a Hugging Face token. A token may be required if downloading from the Hub (private/gated models) or using paid services.
- Models are loaded lazily on first use. Ensure sufficient RAM/VRAM or select a small model.

Environment loading
- SemFire reads a local project `.env` (repo root) and `~/.semfire/.env` if present. Keys are not persisted by the app.

Configuration file (optional)
- A JSON config at `~/.semfire/config.json` (override with `SEMFIRE_CONFIG`) can set provider and models. Example:

```json
{
  "provider": "gemini",
  "gemini": { "api_key_env": "GEMINI_API_KEY", "model": "gemini-1.5-flash-latest" }
}
```

You can also write config programmatically:

```python
from detectors.llm_provider import write_config
write_config("openai", openai_model="gpt-4o-mini")
# Configure transformers provider
write_config(
  "transformers",
  transformers_model_path="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
  transformers_device="cpu"
)
```
